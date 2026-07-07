#!/usr/bin/env python3
"""
Quick Data Profiler

Generates a JSON profile of a tabular dataset covering shape, types,
missing values, basic stats, and duplicate detection.

Usage:
    python scripts/profile_data.py "path/to/data.csv"
    python scripts/profile_data.py "path/to/data.parquet"
    python scripts/profile_data.py "path/to/data.xlsx"

Output: JSON profile printed to stdout.

Exit codes:
    0  success
    1  error (file not found, unsupported format, parse failure)
"""

import json
import sys
from pathlib import Path

import pandas as pd
import numpy as np


def load_data(path: str) -> pd.DataFrame:
    """Load data based on file extension."""
    p = Path(path)
    ext = p.suffix.lower()
    loaders = {
        ".csv": pd.read_csv,
        ".tsv": lambda f: pd.read_csv(f, sep="\t"),
        ".parquet": pd.read_parquet,
        ".xlsx": pd.read_excel,
        ".xls": pd.read_excel,
        ".json": pd.read_json,
    }
    if ext not in loaders:
        print(f"Error: Unsupported file format '{ext}'", file=sys.stderr)
        sys.exit(1)
    return loaders[ext](path)


def profile_column(series: pd.Series) -> dict:
    """Profile a single column."""
    info = {
        "dtype": str(series.dtype),
        "null_count": int(series.isnull().sum()),
        "null_pct": round(series.isnull().mean() * 100, 2),
        "unique_count": int(series.nunique()),
    }
    if pd.api.types.is_numeric_dtype(series):
        desc = series.describe()
        info["stats"] = {
            "mean": round(float(desc.get("mean", 0)), 4),
            "std": round(float(desc.get("std", 0)), 4),
            "min": float(desc.get("min", 0)),
            "25%": float(desc.get("25%", 0)),
            "50%": float(desc.get("50%", 0)),
            "75%": float(desc.get("75%", 0)),
            "max": float(desc.get("max", 0)),
            "skewness": round(float(series.skew()), 4) if len(series.dropna()) > 2 else None,
        }
        # IQR outlier count
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        outliers = ((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum()
        info["outlier_count_iqr"] = int(outliers)
    elif pd.api.types.is_categorical_dtype(series) or series.dtype == "object":
        top = series.value_counts().head(10)
        info["top_values"] = {str(k): int(v) for k, v in top.items()}
        lengths = series.dropna().astype(str).str.len()
        if len(lengths) > 0:
            info["str_length"] = {
                "mean": round(float(lengths.mean()), 1),
                "min": int(lengths.min()),
                "max": int(lengths.max()),
            }
    elif pd.api.types.is_datetime64_any_dtype(series):
        info["date_range"] = {
            "min": str(series.min()),
            "max": str(series.max()),
        }
    return info


def profile_dataframe(df: pd.DataFrame) -> dict:
    """Generate full profile of a DataFrame."""
    profile = {
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": {},
    }
    for col in df.columns:
        profile["columns"][col] = profile_column(df[col])
    return profile


def main():
    if len(sys.argv) < 2:
        print("Usage: python profile_data.py <data-file-path>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    df = load_data(path)

    # Sample if large
    sampled = False
    if len(df) > 50_000:
        df = df.sample(n=50_000, random_state=42)
        sampled = True

    profile = profile_dataframe(df)
    profile["sampled"] = sampled

    print(json.dumps(profile, indent=2, default=str))


if __name__ == "__main__":
    main()
