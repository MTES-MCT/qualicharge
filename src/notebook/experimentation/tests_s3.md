---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.2
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

```python
"""QualiCharge S3 tests"""

import os
import pandas as pd
```

```python
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_URL = os.environ.get("S3_URL", None)
```

```python
expected_path = ["qualicharge-sessions/2025/7/5/staging.parquet",
                 "qualicharge-sessions/2025/7/5/production.parquet",
                 "qualicharge-statuses/2025/7/5/staging.parquet",
                 "qualicharge-statuses/2025/7/5/production.parquet"]
dest_path = ["sessions_staging_07_05.parquet",
             "sessions_production_07_05.parquet",
             "statuses_staging_07_05.parquet",
             "statuses_production_07_05.parquet"]
for expect, dest in zip(expected_path, dest_path):
    df = pd.read_parquet(
            f"s3://{expect}",
            engine="pyarrow",
            dtype_backend="pyarrow",
            storage_options={
                "key": AWS_ACCESS_KEY_ID,
                "secret": AWS_SECRET_ACCESS_KEY,
                "endpoint_url": S3_URL
        }
    )
    df.to_parquet(dest, engine="pyarrow")
```

```python
df
```
