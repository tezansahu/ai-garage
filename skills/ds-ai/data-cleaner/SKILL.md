---
name: data-cleaner
description: Opinionated data cleaning pipeline builder for tabular datasets. Trigger when the user asks to "clean this data", "fix this dataset", "handle missing values", "remove duplicates", "preprocess this data", "data wrangling", "normalize columns", "fix data types", "data quality", or provides messy data that needs cleaning before analysis or modeling. Also triggers on "prepare this data for modeling", "data preprocessing pipeline". Detects column types, handles missing values with strategy recommendations, normalizes strings, fixes date parsing, deduplicates rows, and outputs clean data plus a cleaning report.
---

# Data Cleaner

Build a systematic, documented data-cleaning pipeline that turns raw data into analysis-ready datasets.

---

## Workflow

```
1. Load and profile raw data
2. Fix data types
3. Handle missing values
4. Clean string columns
5. Handle duplicates
6. Detect and handle outliers (optional)
7. Validate and export clean data
8. Generate cleaning report
```

---

## Step 1 -- Load and Profile

Use the `eda-autopilot` skill's `profile_data.py` if available, otherwise:
```python
df = pd.read_csv(path)
print(f"Shape: {df.shape}")
print(df.dtypes)
print(df.isnull().sum())
print(df.describe())
```

---

## Step 2 -- Fix Data Types

| Symptom | Fix |
|---|---|
| Numeric column stored as `object` | `pd.to_numeric(col, errors='coerce')` |
| Date column stored as `object` | `pd.to_datetime(col, errors='coerce', infer_datetime_format=True)` |
| Boolean stored as `0/1` int | `col.astype(bool)` if semantically boolean |
| Category with few unique values | `col.astype('category')` |
| ID columns as numeric | Keep as `str` -- never aggregate IDs |

Always log type changes:
```python
cleaning_log = []
cleaning_log.append({"column": col, "action": "type_cast", "from": "object", "to": "float64", "affected_rows": n})
```

---

## Step 3 -- Handle Missing Values

### Decision Framework

| Scenario | Strategy |
|---|---|
| <5% missing, numeric | Median imputation |
| <5% missing, categorical | Mode imputation |
| 5-30% missing, numeric | Median imputation + add `_is_missing` indicator column |
| 5-30% missing, categorical | Mode imputation + add `_is_missing` indicator column |
| >30% missing | Recommend dropping column (flag for user review) |
| MNAR pattern suspected | Flag for domain expert -- do not auto-impute |
| Entire row mostly empty (>50% null) | Drop row |

### Implementation
```python
for col in df.columns:
    pct = df[col].isnull().mean()
    if pct > 0.3:
        cleaning_log.append({"column": col, "action": "drop_column", "reason": f"{pct:.0%} missing"})
        df.drop(columns=[col], inplace=True)
    elif pct > 0.05:
        df[f"{col}_is_missing"] = df[col].isnull().astype(int)
        fill_val = df[col].median() if pd.api.types.is_numeric_dtype(df[col]) else df[col].mode()[0]
        df[col].fillna(fill_val, inplace=True)
    elif pct > 0:
        fill_val = df[col].median() if pd.api.types.is_numeric_dtype(df[col]) else df[col].mode()[0]
        df[col].fillna(fill_val, inplace=True)
```

---

## Step 4 -- Clean String Columns

Apply to all `object` / `string` dtype columns:

1. **Strip whitespace**: `.str.strip()`
2. **Normalize case**: `.str.lower()` (unless case is semantically meaningful)
3. **Replace multiple spaces**: `.str.replace(r'\s+', ' ', regex=True)`
4. **Standardize missing representations**: Replace `"", "N/A", "n/a", "NA", "null", "None", "-", "?"` with `np.nan`
5. **Trim excessive length**: Flag strings > 500 chars as potential data entry errors

For categorical columns with near-duplicates (e.g., "New York" vs "new york" vs "NEW YORK"):
```python
col = col.str.lower().str.strip()
```

---

## Step 5 -- Handle Duplicates

```python
dupes = df.duplicated()
n_dupes = dupes.sum()
if n_dupes > 0:
    # Log before removing
    cleaning_log.append({"action": "remove_duplicates", "rows_removed": int(n_dupes)})
    df = df.drop_duplicates()
```

For partial duplicates (same on key columns but differ on others):
- Ask user which columns define uniqueness.
- Keep first occurrence by default, or most recent if a timestamp exists.

---

## Step 6 -- Outlier Handling (Optional)

Only apply if user requests or if preparing for modeling:

| Method | When |
|---|---|
| IQR clipping | Default -- clip values to [Q1-1.5*IQR, Q3+1.5*IQR] |
| Z-score removal | Remove rows with |z| > 3 for normally distributed features |
| Domain constraints | Apply known valid ranges (e.g., age: 0-120, price: > 0) |

**Never silently remove outliers** -- always log and flag for review.

---

## Step 7 -- Validate and Export

```python
# Final validation
assert df.isnull().sum().sum() == 0, "Unexpected nulls remain"
assert df.duplicated().sum() == 0, "Duplicates remain"

# Export
df.to_csv("cleaned_data.csv", index=False)
df.to_parquet("cleaned_data.parquet", index=False)
```

---

## Step 8 -- Cleaning Report

Generate a markdown report:

```markdown
# Data Cleaning Report

## Summary
- **Input**: [original file] ([rows] rows x [cols] columns)
- **Output**: cleaned_data.csv ([rows] rows x [cols] columns)
- **Rows removed**: [N] ([reason breakdown])
- **Columns removed**: [N] ([names])
- **Columns added**: [N] (missing indicators)

## Cleaning Log
| Step | Column | Action | Details | Affected Rows |
|------|--------|--------|---------|---------------|
| 1 | price | type_cast | object -> float64 | 1,234 |
| 2 | email | drop_column | 85% missing | -- |
| ... | ... | ... | ... | ... |

## Data Quality After Cleaning
- Missing values: 0
- Duplicates: 0
- [Any remaining warnings]
```
