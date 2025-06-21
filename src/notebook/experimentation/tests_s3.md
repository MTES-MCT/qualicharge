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
expected_path = "qualicharge-sessions/2025/5/28/staging.parquet"
```

```python
df = pd.read_parquet(
        f"s3://{expected_path}",
        engine="pyarrow",
        dtype_backend="pyarrow",
        storage_options={
            "key": AWS_ACCESS_KEY_ID,
            "secret": AWS_SECRET_ACCESS_KEY,
            "endpoint_url": S3_URL
    }
)
```

```python
df
```
