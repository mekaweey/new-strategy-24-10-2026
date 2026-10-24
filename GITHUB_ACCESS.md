# GitHub access / الوصول إلى الملفات

This repository is an uncompressed upload of the audit package. The files are at the repository root.

## ملفات Git LFS

GitHub rejects normal files larger than 100 MB, so all `*.parquet` files here are stored with Git LFS (38 files). The two largest are:

- `data_raw/egx_master_daily.parquet` — 109,842,794 bytes
- `data_derived/features_v3_71.parquet` — 106,678,213 bytes

If you use `raw.githubusercontent.com` for any `.parquet` file, you will receive a 134-byte LFS pointer, **not** the data. Use one of these methods:

### 1. Clone with Git LFS

```bash
git lfs install
git clone https://github.com/mekaweey/new-strategy-24-10-2026.git
cd new-strategy-24-10-2026
git lfs pull
```

### 2. Direct GitHub download (serves the actual bytes)

- https://github.com/mekaweey/new-strategy-24-10-2026/raw/refs/heads/main/data_raw/egx_master_daily.parquet
- https://github.com/mekaweey/new-strategy-24-10-2026/raw/refs/heads/main/data_derived/features_v3_71.parquet

These URLs redirect to GitHub's media host and return the original LFS content. Verified SHA256:

- `data_raw/egx_master_daily.parquet`: `9b6664d974f678b55427944177d620b0dd607d01568089f5cec382aa70170fc8`
- `data_derived/features_v3_71.parquet`: `d91f92cd3d2ecfc272a3ea227e095e65cd27f89da8f344076da843b2de3e27a5`

## ملاحظة عن السجل

The original audit project was not a Git repository. This GitHub repository was created for sharing; its Git history starts with the upload, so it is not evidence of the original development history.
