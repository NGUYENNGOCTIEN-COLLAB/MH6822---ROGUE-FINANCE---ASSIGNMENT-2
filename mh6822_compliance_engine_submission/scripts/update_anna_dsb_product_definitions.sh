#!/usr/bin/env bash
#
# Swap the local hand-rolled product-definitions tree for the production
# ANNA-DSB / Product-Definitions distribution.
#
# Usage:
#   bash scripts/update_anna_dsb_product_definitions.sh
#
# Notes:
# * The local tree is backed up to data/product_definitions.bak.<timestamp>
#   so the swap is reversible.
# * The engine picks up the new templates with no code changes; the lookup
#   key is (AssetClass, InstrumentType, UseCase) which the production tree
#   uses identically.

set -euo pipefail

REPO_URL="https://github.com/ANNA-DSB/Product-Definitions.git"
TARGET_DIR="data/product_definitions"
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${TARGET_DIR}.bak.${TS}"

if [ -d "$TARGET_DIR" ]; then
    echo "Backing up existing tree to $BACKUP_DIR"
    cp -r "$TARGET_DIR" "$BACKUP_DIR"
fi

# The ANNA-DSB tree does not have a stable LICENSE on this path; we clone
# the default branch (main).
echo "Cloning $REPO_URL into $TARGET_DIR"
rm -rf "$TARGET_DIR"
git clone --depth=1 "$REPO_URL" "$TARGET_DIR"

# Sanity check: verify the standard PROD/OTC-Products subtree is present.
EXPECTED="$TARGET_DIR/PROD/OTC-Products/UPI"
if [ ! -d "$EXPECTED" ]; then
    echo "ERROR: cloned tree does not contain expected subtree at $EXPECTED"
    echo "       Restoring backup..."
    rm -rf "$TARGET_DIR"
    mv "$BACKUP_DIR" "$TARGET_DIR"
    exit 1
fi

echo "ANNA-DSB Product-Definitions installed at $TARGET_DIR"
echo "Run the engine with the same command - no code changes required."
echo "  python run_compliance_check.py --input trades.json --regimes CFTC,EMIR"
