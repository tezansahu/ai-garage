# EDA Checklist

Every EDA must cover these sections. Skip a section only if genuinely not applicable.

---

## 1. Dataset Shape & Types

- Print `.shape`, `.dtypes`, `.info()`.
- Classify columns: numeric (continuous vs discrete), categorical (nominal vs ordinal), datetime, text, ID/key.
- Flag columns with suspicious types (e.g., numeric stored as string).

## 2. Missing Values

- Heatmap or bar chart of missing percentages per column.
- Identify patterns: MCAR, MAR, or MNAR (note evidence).
- List columns with >30% missing -- recommend drop vs. impute.

## 3. Univariate Analysis

### Numeric columns
- Histogram + KDE overlay for each (or a grid if many).
- Box plot or violin plot for outlier visibility.
- Report skewness and kurtosis; flag highly skewed columns.
- Summary stats table: count, mean, std, min, 25%, 50%, 75%, max.

### Categorical columns
- Bar chart of value counts (top 15 if high cardinality).
- Report cardinality; flag columns with >50 unique values.
- Identify rare categories (<1% frequency).

### Datetime columns
- Time series line plot if target exists.
- Distribution of records over time (histogram by month/week).
- Flag gaps or irregular intervals.

## 4. Bivariate Analysis

### Numeric vs Numeric
- Correlation matrix heatmap (Pearson + Spearman if non-linear suspected).
- Scatter plots for top correlated pairs (|r| > 0.6).
- Flag multicollinearity (|r| > 0.9).

### Numeric vs Categorical
- Box plots of numeric feature grouped by top categories.
- ANOVA or Kruskal-Wallis test for significance.

### Categorical vs Categorical
- Contingency table / heatmap for top category pairs.
- Chi-squared test for independence where relevant.

## 5. Target Variable Deep Dive (if applicable)

- Distribution of target (class balance for classification, distribution for regression).
- Correlation of all features with target, sorted by absolute value.
- Top 5 most predictive features (mutual information or correlation).

## 6. Outlier Detection

- IQR method: flag values < Q1-1.5*IQR or > Q3+1.5*IQR.
- Z-score method for normally distributed features.
- Report count and percentage of outliers per column.
- Visualize outliers in context (scatter or box plot).

## 7. Multivariate Analysis

- Pair plot for top 5-8 numeric features (colored by target if available).
- PCA or t-SNE 2D projection for high-dimensional data.
- Cluster tendency visualization if unsupervised task.

## 8. Data Quality Summary Table

| Column | Type | Nulls (%) | Unique | Outliers | Notes |
|---|---|---|---|---|---|
| col_name | numeric | 5.2% | 342 | 12 (IQR) | Right-skewed |
