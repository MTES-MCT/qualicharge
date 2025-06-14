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
import sys
sys.path.append('/home/jovyan/work') 
sys.path.append('/home/jovyan/work/src') 
sys.path.append('/home/jovyan/work/src/prefect') 
sys.path.append('/home/jovyan/work/src/prefect/cooling') 
```

```python
"""QualiCharge prefect cooling tests: statuses."""

import os
import pandas as pd

os.getenv("S3_ENDPOINT_URL")
```

```python
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
```

```python
expected_path = "qualicharge-sessions/2025/5/28/staging.parquet"
s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", "http://minio:9000")
```

```python
print(s3_endpoint_url)
```

```python
df = pd.read_parquet(
        f"s3://{expected_path}",
        engine="pyarrow",
        dtype_backend="pyarrow",
        storage_options={
            "endpoint_url": s3_endpoint_url,
        },
    )
```

```python
http://127.0.0.1:8888/lab/tree/work/src/notebook/experimentation/tests_s3.ipynb
http://minio:9000/qualicharge-sessions/2025/5/28/staging.parquet
#"client_kwargs": {"endpoint_url": "http://172.17.0.2:9000"}
#"client_kwargs": {"endpoint_url": "http://127.0.0.1:9001"}
#"client_kwargs": {"endpoint_url": "http://minio:9001"}
```

```python
df = pd.read_parquet(
    "s3://qualicharge-sessions/2025/5/28/staging.parquet",
        engine="pyarrow",
        dtype_backend="pyarrow",
        storage_options={
            "key": AWS_ACCESS_KEY_ID,
            "secret": AWS_SECRET_ACCESS_KEY,
            "endpoint_url": "http://172.17.0.2:9000"
    }
)
```
