"""MH6822 OTC Derivatives Compliance Engine.

Public exports re-exposed for convenience::

    from compliance_engine import parse_trade, lookup_upi, check_compliance
"""

from .module1_parser import parse_trade, parse_portfolio, classify_instrument  # noqa: F401
from .module2_upi_lookup import lookup_upi, TemplateLibrary  # noqa: F401
from .module3_compliance import check_compliance  # noqa: F401

__all__ = [
    "parse_trade",
    "parse_portfolio",
    "classify_instrument",
    "lookup_upi",
    "TemplateLibrary",
    "check_compliance",
]
