---
jupyter:
  jupytext:
    formats: ipynb,md
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

# Scalingo logs parser

The aim of this notebook is to analyze API server logs and check API performances and usage.

```python
import gzip
import re
import pandas as pd

from datetime import datetime

# Regular expression to remove ainsi colors
# https://stackoverflow.com/a/14693789
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# Regular expression to pre-parse Scalingo logs
# Separate timestamp from logfmt string
scalingo_pattern = r"(?P<timestamp>.*) CET \[router\] (?P<logfmt>.*)"

# Regular expression to parse logfmt
#
# Example value:
#
# method=POST \
#   path="/api/v1/dynamique/status/" \
#   host=staging.qualicharge.incubateur.net \
#   request_id=43cab79a-3e71-4683-b400-d6fb3aab4eea \
#   container=web-1 from="xxx.xxx.xxx.xxx" \
#   protocol=https \
#   status=201 \
#   duration=0.029s \
#   bytes=512 \
#   referer="-" \
#   user_agent="Go-http-client/1.1"
logfmt_pattern = r'([\w.]+)\s*=\s*(?:"((?:[^"\\]|\\.)*)"|([^\s]*))'
```

```python
def log2records(log_file_path):

    with gzip.open(log_file_path) as log_file:
        for line in log_file:
            # Remove ainsi colors
            raw = ansi_escape.sub('', line.decode('utf-8'))

            # The date time string is odd...
            m = re.match(scalingo_pattern, raw)

            # We only want router events
            if not m:
                continue

            timestamp = pd.to_datetime(m.group("timestamp"))
            logs = m.group("logfmt")

            # Create record
            parsed_logs = [[m[0], m[1] if m[1] else m[2]] for m in re.findall(logfmt_pattern, logs)]
            record = {k: v for k,v in parsed_logs}
            record["timestamp"] = timestamp
            yield record
```

```python
# Load log file
logs = pd.DataFrame.from_records(log2records("../../../data/65fdc9d0fb0de6000e1e9ce1.log-2025012418.gz"))
logs
```

```python
# Fix duration type
logs["duration"] = logs["duration"].apply(lambda x: x[:-1]).astype(float)
logs["duration"]
```

```python
# SELECT ONLY /api/v1/ queries and ignore 307 responses
logs = logs[logs["path"].str.contains("/api/v1")]
logs = logs[logs["status"].astype(int) != 307]
logs
```

```python
# Response duration distribution given API endpoint
logs.hist(column="duration", by=["method","path"], layout=(20,3), figsize=(15, 60), sharex=False, bins=20, backend="matplotlib")
```

```python
# Response duration > 1 sec distribution given API endpoint
logs[logs["duration"] > 1].hist(column="duration", by=["method","path"], layout=(20,3), figsize=(15, 60), sharex=False, bins=20, backend="matplotlib")
```

```python
len(logs[logs["duration"] > 1])
```
