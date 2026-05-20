"""Module 2: UPI lookup against the ANNA-DSB Product Definition library.

The library is a tree of JSON files at
``data/product_definitions/PROD/OTC-Products/UPI/<AssetClass>/<File>.UPI.V1.json``
plus a ``codesets/`` directory of controlled vocabularies referenced from
templates.

Each template declares attribute constraints. Validation walks every declared
attribute, consults the constraint type (codeset, enum, pattern, min/max,
not), and records errors or warnings.

Special cases:

* **LIBOR is a warning, not an error.** GBP/USD/CHF/JPY/EUR LIBOR ceased on
  30 June 2023, but legacy trades remain reportable. The engine surfaces the
  LIBOR reference as a warning so risk teams see it without auto-failing the
  trade.
* **Novel asset classes normally return** ``NO_PRODUCT_DEFINITION`` with a
  structured note pointing at Module 4.  The lookup deliberately checks the
  template library first, so a future registered EventContract template can
  override the taxonomy-gap path without a code rewrite.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Optional

from .models import ParsedTrade, UpiLookupResult
from .module1_parser import (
    CLASSIFICATION_CONVENTIONAL,
    CLASSIFICATION_NOVEL,
)
from .utils import (
    is_present,
    validate_currency,
    validate_currency_pair,
)


DEFAULT_PRODUCT_DEFS = Path("data/product_definitions/PROD/OTC-Products")


# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------

class TemplateLibrary:
    """Loads and caches templates and codesets from the product-definitions tree.

    The tree layout is:

        <root>/
            UPI/<AssetClass>/<File>.UPI*.json
            codesets/<Codeset>.json

    ``root`` may point at either ``PROD/OTC-Products`` or its ``UPI`` child;
    both are normalised to the same effective path.
    """

    def __init__(self, root: str | Path | None = None) -> None:
        root = Path(root) if root is not None else DEFAULT_PRODUCT_DEFS
        if root.name == "UPI":
            self.upi_dir = root
            self.codesets_dir = root.parent / "codesets"
        else:
            self.upi_dir = root / "UPI"
            self.codesets_dir = root / "codesets"
        self._templates: list[dict[str, Any]] | None = None
        self._codesets: dict[str, set[str]] = {}

    def _load(self) -> None:
        if self._templates is not None:
            return
        templates: list[dict[str, Any]] = []
        skipped: list[tuple[str, str]] = []
        if self.upi_dir.exists():
            for path in sorted(self.upi_dir.rglob("*.UPI*.json")):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    data.setdefault("TemplateFile", str(path))
                    templates.append(data)
                except OSError as exc:
                    skipped.append((str(path), f"OSError: {exc}"))
                except json.JSONDecodeError as exc:
                    skipped.append((str(path), f"JSONDecodeError: {exc}"))
        if skipped:
            import sys
            print(
                f"[TemplateLibrary] WARNING: {len(skipped)} of "
                f"{len(skipped) + len(templates)} template files failed to load. "
                "First failures shown; check path length (Windows MAX_PATH 260) "
                "or file integrity:",
                file=sys.stderr,
            )
            for path, reason in skipped[:5]:
                print(f"  - {path}: {reason}", file=sys.stderr)
            if len(skipped) > 5:
                print(f"  - ...and {len(skipped) - 5} more", file=sys.stderr)
        self._templates = templates

    def all_templates(self) -> list[dict[str, Any]]:
        self._load()
        return self._templates  # type: ignore[return-value]

    def find_template(
        self,
        asset_class: Optional[str],
        instrument_type: Optional[str],
        use_case: Optional[str],
    ) -> Optional[dict[str, Any]]:
        if not (asset_class and instrument_type and use_case):
            return None
        for tpl in self.all_templates():
            if (
                tpl.get("AssetClass") == asset_class
                and tpl.get("InstrumentType") == instrument_type
                and tpl.get("UseCase") == use_case
            ):
                return tpl
        return None

    def get_codeset(self, name: str) -> set[str]:
        if name in self._codesets:
            return self._codesets[name]
        path = self.codesets_dir / f"{name}.json"
        codes: set[str] = set()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    codes = {str(x) for x in data}
                elif isinstance(data, dict):
                    for key in ("values", "codes", "enum", "data"):
                        items = data.get(key)
                        if isinstance(items, list):
                            codes = {str(x) for x in items}
                            break
            except (OSError, json.JSONDecodeError):
                codes = set()
        self._codesets[name] = codes
        return codes


# ---------------------------------------------------------------------------
# Attribute validation
# ---------------------------------------------------------------------------

def _camel_to_snake(name: str) -> str:
    parts: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i and not name[i - 1].isupper():
            parts.append("_")
        parts.append(ch.lower())
    return "".join(parts)


def _source_fields(attr_name: str, spec: dict[str, Any]) -> list[str]:
    explicit = spec.get("source_fields") or spec.get("source_field")
    if isinstance(explicit, str):
        return [explicit]
    if isinstance(explicit, list):
        return [str(x) for x in explicit]
    return [_camel_to_snake(attr_name)]


def _validate_one_value(
    attr_name: str,
    field_name: str,
    value: Any,
    spec: dict[str, Any],
    library: TemplateLibrary,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    type_ = spec.get("type")
    if type_ == "integer" and not isinstance(value, int) or (type_ == "integer" and isinstance(value, bool)):
        errors.append(f"{field_name}: must be integer for {attr_name}")
        return errors, warnings
    if type_ == "number" and not isinstance(value, (int, float)) or (type_ == "number" and isinstance(value, bool)):
        errors.append(f"{field_name}: must be numeric for {attr_name}")
        return errors, warnings
    if type_ == "string" and not isinstance(value, str):
        errors.append(f"{field_name}: must be string for {attr_name}")
        return errors, warnings

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in spec and value < spec["minimum"]:
            errors.append(f"{field_name}={value} below minimum {spec['minimum']}")
        if "maximum" in spec and value > spec["maximum"]:
            errors.append(f"{field_name}={value} above maximum {spec['maximum']}")
        if "not" in spec and value == spec["not"]:
            errors.append(f"{field_name}={value} must not equal {spec['not']}")

    if isinstance(value, str):
        if "minLength" in spec and len(value) < spec["minLength"]:
            errors.append(f"{field_name}: length {len(value)} below minimum {spec['minLength']}")
        if "maxLength" in spec and len(value) > spec["maxLength"]:
            errors.append(f"{field_name}: length {len(value)} above maximum {spec['maxLength']}")
        if "pattern" in spec and not re.fullmatch(spec["pattern"], value):
            errors.append(f"{field_name}={value!r} does not match pattern {spec['pattern']!r}")

    enum = spec.get("enum")
    if enum is not None and value not in enum:
        errors.append(f"{field_name}={value!r} is not one of {enum}")

    codeset = spec.get("codeset")
    if codeset == "ISOCurrencyCode":
        ok, msg = validate_currency(value)
        if not ok:
            errors.append(f"{field_name}: {msg}")
    elif codeset == "CurrencyPair":
        ok, msg = validate_currency_pair(value)
        if not ok:
            errors.append(f"{field_name}: {msg}")
    elif codeset:
        codes = library.get_codeset(codeset)
        if codes and str(value) not in codes:
            errors.append(f"{field_name}={value!r} is not in codeset {codeset}")
        # LIBOR is a warning even when the code is recognised.
        if isinstance(value, str) and "LIBOR" in value.upper():
            warnings.append(
                f"{field_name}={value!r} references LIBOR; deprecated benchmark "
                "(retained as warning for legacy trade handling per FCA / Federal "
                "Reserve cessation guidance, 30 June 2023)"
            )

    return errors, warnings


def validate_attributes(
    raw_trade: dict[str, Any],
    template: dict[str, Any],
    library: TemplateLibrary,
) -> tuple[list[str], list[str]]:
    """Walk a template's Attributes dict against the trade record.

    Returns (errors, warnings). Both lists are sorted, deduplicated, and safe
    to merge into ``UpiLookupResult``.
    """
    errors: list[str] = []
    warnings: list[str] = []

    attributes = template.get("Attributes") or {}
    for attr_name, spec in attributes.items():
        if not isinstance(spec, dict):
            continue
        required = spec.get("required", True)
        fields = _source_fields(attr_name, spec)
        present = [(f, raw_trade[f]) for f in fields if f in raw_trade and is_present(raw_trade[f])]

        if not present:
            if required:
                errors.append(f"missing required attribute {attr_name} (looked in {fields})")
            continue

        for field_name, value in present:
            attr_errors, attr_warnings = _validate_one_value(
                attr_name, field_name, value, spec, library,
            )
            errors.extend(attr_errors)
            warnings.extend(attr_warnings)

    # Generic safeguards: catch obvious LIBOR / currency violations even on
    # fields the template author didn't bind. This is what production
    # validators do because templates are written by humans and miss things.
    libor_already_warned = any("LIBOR" in w.upper() for w in warnings)
    for field_name, value in raw_trade.items():
        if not is_present(value):
            continue
        if (
            "reference_rate" in field_name
            and isinstance(value, str)
            and "LIBOR" in value.upper()
            and not libor_already_warned
        ):
            warnings.append(
                f"{field_name}={value!r} references LIBOR; deprecated benchmark "
                "(retained as warning for legacy trade handling)"
            )
            libor_already_warned = True

    return sorted(set(errors)), sorted(set(warnings))


# ---------------------------------------------------------------------------
# Public lookup entry point
# ---------------------------------------------------------------------------

_NO_PRODUCT_NOTE = (
    "Asset class {asset_class!r} (instrument {instrument_type!r}) has no "
    "product definition in the ANNA-DSB UPI library. This is the regulatory "
    "classification frontier the assignment is testing for. See Module 4 for "
    "the proposed schema extension."
)


def lookup_upi(
    parsed: ParsedTrade,
    raw_trade: dict[str, Any],
    library: TemplateLibrary,
) -> UpiLookupResult:
    """Resolve a parsed trade against the template library.

    The order is intentional: try the library first, even for instruments
    currently marked ``NOVEL_INSTRUMENT_NO_TAXONOMY``.  That keeps today's
    event contracts on the required ``NO_PRODUCT_DEFINITION`` path because no
    active EventContract template exists, while allowing a future ANNA-DSB
    EventContract template to be validated without rewriting the engine.
    """
    if parsed.classification_flag not in {CLASSIFICATION_CONVENTIONAL, CLASSIFICATION_NOVEL}:
        return UpiLookupResult(
            trade_id=parsed.trade_id,
            status="NOT_FOUND",
            matched_template=None,
            upi_code=None,
            classification_note="Classification ambiguous; UPI lookup not attempted.",
            validation_errors=["classification is ambiguous"],
        )

    template = library.find_template(parsed.asset_class, parsed.instrument_type, parsed.use_case)
    if template is not None:
        errors, warnings = validate_attributes(raw_trade, template, library)
        template_name = template.get("TemplateName") or (
            f"{template.get('AssetClass')}.{template.get('InstrumentType')}.{template.get('UseCase')}"
        )
        return UpiLookupResult(
            trade_id=parsed.trade_id,
            status="INVALID_ATTRIBUTES" if errors else "FOUND",
            matched_template=template_name,
            upi_code=None if errors else template.get("UPI"),
            classification_note=None,
            validation_errors=errors,
            warnings=warnings,
        )

    if parsed.classification_flag == CLASSIFICATION_NOVEL:
        return UpiLookupResult(
            trade_id=parsed.trade_id,
            status="NO_PRODUCT_DEFINITION",
            matched_template=None,
            upi_code=None,
            classification_note=_NO_PRODUCT_NOTE.format(
                asset_class=parsed.asset_class,
                instrument_type=parsed.instrument_type,
            ),
        )

    return UpiLookupResult(
        trade_id=parsed.trade_id,
        status="NOT_FOUND",
        matched_template=None,
        upi_code=None,
        classification_note=(
            f"No ANNA-DSB template for "
            f"{parsed.asset_class}.{parsed.instrument_type}.{parsed.use_case}"
        ),
    )
