---
name: data-analysis
description: Use this skill when the user wants to analyze data, create reports from CSV/Excel files, compute statistics, visualize trends, or summarize datasets. If the user mentions data analysis, financial reports, revenue analysis, or asks to process tabular data, use this skill.
license: MIT
---

# Data Analysis Toolkit

## Overview

This skill provides utilities for analyzing CSV and Excel data, generating summary reports, and computing key metrics. It supports financial data, sales reports, inventory tracking, and general tabular analysis.

## Quick Start

```python
import pandas as pd

# Load data
df = pd.read_csv("data.csv")

# Quick summary
print(df.describe())
print(df.info())
```

## Analysis Workflow

### Step 1: Load and Inspect Data

```python
import pandas as pd

df = pd.read_csv("input.csv")

# Check structure
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(df.head())
print(df.dtypes)
```

### Step 2: Clean Data

```python
# Handle missing values
df = df.dropna(subset=["revenue"])  # Drop rows missing revenue
df["category"] = df["category"].fillna("Unknown")

# Convert types
df["date"] = pd.to_datetime(df["date"])
df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
```

### Step 3: Compute Metrics

```python
# Summary statistics
total_revenue = df["revenue"].sum()
avg_revenue = df["revenue"].mean()
median_revenue = df["revenue"].median()

# Group analysis
by_category = df.groupby("category")["revenue"].agg(["sum", "mean", "count"])
by_month = df.groupby(df["date"].dt.to_period("M"))["revenue"].sum()
```

### Step 4: Generate Report

```python
# Write report
with open("report.md", "w") as f:
    f.write("# Analysis Report\n\n")
    f.write(f"**Total Revenue:** ${total_revenue:,.2f}\n")
    f.write(f"**Average:** ${avg_revenue:,.2f}\n")
    f.write(f"**Records:** {len(df)}\n\n")
    f.write("## By Category\n\n")
    f.write(by_category.to_markdown())
```

## Helper Scripts

The `scripts/` directory contains analysis utilities:

- **`analyze.py`** — Automated analysis pipeline. Reads a CSV, computes summary statistics, and generates a formatted report. Usage:

  ```bash
  python scripts/analyze.py input.csv report.md
  ```

  This handles data loading, cleaning, metric computation, and report formatting in one step. Recommended for standard analysis tasks.

## Financial Analysis

### Key Metrics

```python
# Revenue metrics
gross_margin = (revenue - cogs) / revenue
yoy_growth = (current_year - prior_year) / prior_year
run_rate = quarterly_revenue * 4

# Variance analysis
budget_variance = (actual - budget) / budget
```

### Common Aggregations

```python
# Monthly trends
monthly = df.resample("M", on="date")["revenue"].sum()

# Top performers
top_10 = df.nlargest(10, "revenue")

# Distribution
quartiles = df["revenue"].quantile([0.25, 0.5, 0.75])
```

## Output Formats

### Markdown Report
```python
report = f"""# Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d')}

## Summary
- Total: ${total:,.2f}
- Mean: ${mean:,.2f}
- Median: ${median:,.2f}

## Details
{details_table.to_markdown()}
"""
```

### CSV Export
```python
results.to_csv("output.csv", index=False)
```

## Dependencies

```bash
pip install pandas openpyxl
```
