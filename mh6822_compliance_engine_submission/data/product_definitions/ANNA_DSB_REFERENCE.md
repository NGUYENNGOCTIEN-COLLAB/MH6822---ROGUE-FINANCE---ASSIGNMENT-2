# ANNA-DSB Product-Definitions reference

The active product-definition tree in this repository is a deterministic ANNA-DSB-style fixture used for reproducible grading on the MH6822 Homework 2 portfolio.

Production source repository:

```text
https://github.com/ANNA-DSB/Product-Definitions
```

To replace the fixture with the production repository in a network-enabled environment, run:

```bash
bash scripts/update_anna_dsb_product_definitions.sh
```

The engine expects the following layout:

```text
data/product_definitions/PROD/OTC-Products/UPI/<AssetClass>/*.UPI*.json
data/product_definitions/PROD/OTC-Products/codesets/*.json
```
