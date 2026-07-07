---
name: eda-autopilot
description: Perform comprehensive Exploratory Data Analysis on any tabular dataset (CSV, Parquet, Excel, or database table). Trigger when the user asks to "explore this data", "run EDA", "analyze this dataset", "what's in this data", "profile this CSV", "show me distributions", "find patterns in this data", or provides a data file and wants to understand its contents. Also triggers on requests to check data quality, find outliers, or understand feature relationships. Generates a complete EDA notebook or script with visualizations, statistical summaries, and a written findings report.
---

# EDA Autopilot

Generate a thorough, publication-ready Exploratory Data Analysis from any tabular dataset.

---

## Workflow

```
1. Detect data source and load dataset
2. Run profiling script (scripts/profile_data.py)
3. Generate EDA notebook or script with full analysis
4. Produce summary findings report
```

---

## Step 1 -- Detect Data Source

| Input | Action |
|---|---|
| `.csv` file path | `pd.read_csv(path)` |
| `.parquet` file path | `pd.read_parquet(path)` |
| `.xlsx` / `.xls` file path | `pd.read_excel(path)` |
| SQL table name + connection string | `pd.read_sql(query, conn)` |
| DataFrame already in memory | Use as-is |

If the file is large (>100 MB), sample 50k rows for profiling and note this in the report.

---

## Step 2 -- Run Data Profiling

```bash
python <skill-path>/scripts/profile_data.py "<data-file-path>"
```

The script outputs a JSON profile to stdout with:
- Row count, column count, memory usage
- Per-column: dtype, nulls, unique count, top values, basic stats (mean/median/std/min/max for numeric; lengths for string)
- Duplicate row count

Use this profile to inform the full EDA.

---

## Step 3 -- Generate EDA

Read `references/eda-checklist.md` for the required analysis sections.

Core principles:
- **Every chart must have a title, axis labels, and a one-sentence interpretation.**
- Use Plotly for interactive charts when in a notebook; fall back to Matplotlib/Seaborn for scripts.
- Group analysis logically: univariate -> bivariate -> multivariate.
- Flag anomalies explicitly with clear callouts.
- If a target variable is identified, orient analysis around its relationship with features.

---

## Step 4 -- Summary Report

Produce a markdown summary at the end of the notebook / as a standalone file:

```markdown
# EDA Summary: [Dataset Name]

## Dataset Overview
- Rows: X | Columns: Y | Memory: Z MB
- Time range: [if applicable]

## Data Quality
- Missing values: [summary]
- Duplicates: X rows
- Outliers detected: [columns + method]

## Key Findings
1. [Most important pattern or insight]
2. [Second finding]
3. [Third finding]

## Recommendations
- [Data cleaning steps to take]
- [Features worth engineering]
- [Potential modeling approaches based on data characteristics]
```

---

## Library Preferences

| Purpose | Library | Fallback |
|---|---|---|
| Data manipulation | `pandas` | `polars` |
| Quick profiling | `scripts/profile_data.py` | `ydata-profiling` |
| Static plots | `matplotlib` + `seaborn` | -- |
| Interactive plots | `plotly.express` | -- |
| Correlation | `pandas .corr()` | `phik` for mixed types |
