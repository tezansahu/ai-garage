---
name: feature-forge
description: Generate and engineer features from raw tabular data for machine learning. Trigger when the user asks to "engineer features", "create features", "feature engineering", "generate features", "transform features", "feature extraction", "build feature matrix", or mentions lag features, rolling averages, interaction terms, target encoding, cyclical encoding, text features, or date features. Also triggers on "improve model with better features", "what features should I create", or "feature ideas for this data". Supports numeric, categorical, datetime, and text feature engineering patterns.
---

# Feature Forge

Systematically generate high-value features from raw data to improve model performance.

---

## Workflow

```
1. Profile input data (column types, cardinality, patterns)
2. Apply feature engineering recipes by column type
3. Generate feature importance preview
4. Output feature matrix + documentation
```

---

## Step 1 -- Profile for Feature Opportunities

For each column, identify:
- Type: numeric, categorical, datetime, text, boolean, ID (skip IDs)
- Cardinality: low (<15), medium (15-100), high (>100)
- Distribution: skewed, normal, uniform, sparse
- Relationships: known domain relationships between columns

---

## Step 2 -- Feature Engineering Recipes

### Numeric Features

| Recipe | When to apply | Code pattern |
|---|---|---|
| **Log transform** | Right-skewed (skew > 1) | `np.log1p(col)` |
| **Square root** | Count data | `np.sqrt(col)` |
| **Binning** | Non-linear relationship with target | `pd.cut(col, bins=5, labels=False)` |
| **Polynomial** | Suspected non-linear effects | `col**2`, `col**3` |
| **Interaction terms** | Two features that multiply meaningfully | `col_a * col_b` |
| **Ratio features** | Meaningful business ratios | `col_a / (col_b + 1e-8)` |
| **Clipping** | Outlier-sensitive models | `col.clip(lower=q01, upper=q99)` |
| **Rank transform** | Highly skewed, ordinal matters | `col.rank(pct=True)` |
| **Standard scaling** | For distance-based models | `(col - mean) / std` |

### Categorical Features

| Recipe | When to apply | Code pattern |
|---|---|---|
| **One-hot encoding** | Low cardinality (<=15) | `pd.get_dummies(col)` |
| **Ordinal encoding** | Ordered categories (size: S<M<L) | Manual mapping dict |
| **Target encoding** | High cardinality + target available | `col.map(target_means)` with smoothing |
| **Frequency encoding** | High cardinality, count matters | `col.map(col.value_counts(normalize=True))` |
| **Binary encoding** | Medium cardinality (15-100) | `category_encoders.BinaryEncoder` |
| **Hash encoding** | Very high cardinality (>1000) | `category_encoders.HashingEncoder(n_components=8)` |
| **Rare category grouping** | Categories with <1% frequency | Group into "Other" |

### DateTime Features

| Recipe | Code pattern |
|---|---|
| **Basic extraction** | `year, month, day, hour, minute, dayofweek, quarter` |
| **Cyclical encoding (hour)** | `sin(2*pi*hour/24)`, `cos(2*pi*hour/24)` |
| **Cyclical encoding (month)** | `sin(2*pi*month/12)`, `cos(2*pi*month/12)` |
| **Cyclical encoding (dayofweek)** | `sin(2*pi*dow/7)`, `cos(2*pi*dow/7)` |
| **Is weekend** | `dayofweek >= 5` |
| **Is business hour** | `9 <= hour <= 17` |
| **Days since reference** | `(date - reference_date).dt.days` |
| **Time since last event** | `date.diff()` |
| **Part of month** | `day <= 10: "start"`, `day <= 20: "mid"`, else `"end"` |

### Time Series / Sequential Features

| Recipe | When to apply | Code pattern |
|---|---|---|
| **Lag features** | Temporal dependence | `col.shift(1)`, `col.shift(7)` |
| **Rolling mean** | Smooth trends | `col.rolling(window=7).mean()` |
| **Rolling std** | Volatility | `col.rolling(window=7).std()` |
| **Expanding mean** | Cumulative behavior | `col.expanding().mean()` |
| **Diff features** | Rate of change | `col.diff(1)` |
| **Pct change** | Relative rate of change | `col.pct_change(1)` |
| **EWM** | Recent-weighted trends | `col.ewm(span=7).mean()` |

### Text Features

| Recipe | When to apply | Code pattern |
|---|---|---|
| **Char count** | Always for text | `col.str.len()` |
| **Word count** | Always for text | `col.str.split().str.len()` |
| **Sentence count** | Long text | `col.str.count(r'[.!?]+')` |
| **Contains keyword** | Domain-specific keywords | `col.str.contains('keyword', case=False)` |
| **TF-IDF** | Text as primary input | `TfidfVectorizer(max_features=100)` |
| **Embeddings** | Semantic understanding needed | Use sentence-transformers |

---

## Step 3 -- Feature Importance Preview

After generating features, provide a quick importance check:

```python
from sklearn.ensemble import RandomForestClassifier  # or Regressor
from sklearn.inspection import permutation_importance

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Built-in importance
importance = pd.Series(model.feature_importances_, index=X_train.columns)
print(importance.sort_values(ascending=False).head(20))
```

Drop features with near-zero importance to keep the feature matrix manageable.

---

## Step 4 -- Output

Save:
- **Feature matrix**: `features.parquet` (or `.csv`)
- **Feature documentation**: `feature_definitions.md`

### Feature Documentation Template

```markdown
# Feature Definitions

## Source Dataset
- **File**: [original data file]
- **Rows**: [N] | **Original Columns**: [N] | **Engineered Features**: [N]

## Feature Registry

| Feature Name | Source Column(s) | Type | Description | Recipe |
|---|---|---|---|---|
| price_log | price | numeric | Log-transformed price | `np.log1p(price)` |
| city_target_enc | city | numeric | Target-encoded city | Target mean with smoothing |
| hour_sin | timestamp | numeric | Cyclical hour (sin) | `sin(2*pi*hour/24)` |
```

---

## Guardrails

- **No target leakage**: Never use future information or the target itself as a feature.
- **Fit on train only**: All encoding (target encoding, scaling) must fit on training data only.
- **Document everything**: Every engineered feature must have a clear name and description.
- **Don't over-engineer**: Start with 10-20 well-chosen features rather than 200 kitchen-sink features.
