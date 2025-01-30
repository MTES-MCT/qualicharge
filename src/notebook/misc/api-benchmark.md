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

# QualiCharge API performance assessment

This notebook aims at analyzing and track changes in API performance.

## Load dataset

```python
import pandas as pd
```

```python
bench = pd.read_csv("../../../data/bench.csv", dtype_backend="pyarrow")
bench
```

## Statistical analysis

```python
import seaborn as sns
```

```python
stats = bench.copy()
stats.dropna(how="any", axis=0, inplace=True)
stats["endpoint"] = stats["Name"] + " " + stats["Type"]
stats
```

```python
sns.relplot(data=stats, x="Request Count", y="Median Response Time", hue="timestamp", col="endpoint", col_wrap=4, legend="full")
```

As Response time is directly correlated to the number of request ran, let's try to normalize the first by the later and analyze distribution.

```python
stats["ratio_average"] = stats["Average Response Time"] / stats["Request Count"]
stats["ratio_median"] = stats["Median Response Time"] / stats["Request Count"]
stats
```

```python
import matplotlib.pyplot as plt
f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
f.set_figwidth(20)

# Median
sns.boxplot(data=stats, x="ratio_median", y="endpoint", ax=ax1, color="whitesmoke")
sns.stripplot(data=stats, x="ratio_median", y="endpoint", hue="timestamp", jitter=0, ax=ax1, legend=False)
ax1.set_xlabel("Ratio (Median)")

# Mean
sns.boxplot(data=stats, x="ratio_average", y="endpoint", ax=ax2, color="whitesmoke")
sns.stripplot(data=stats, x="ratio_average", y="endpoint", hue="timestamp", jitter=0, ax=ax2, legend=True)
ax2.set_xlabel("Ratio (Average)")
```
