# Chart Selector

Use this decision tree to pick the right chart type. When in doubt, prefer simpler charts.

---

## By Number of Variables

### One Variable (Univariate)

| Data type | Chart | When |
|---|---|---|
| Numeric (continuous) | **Histogram** | Show distribution shape |
| Numeric (continuous) | **KDE plot** | Smooth distribution, compare groups |
| Numeric (continuous) | **Box plot** | Show median, quartiles, outliers |
| Numeric (continuous) | **Violin plot** | Distribution + density combination |
| Categorical | **Bar chart** (horizontal) | Compare counts across categories |
| Categorical (ordered) | **Bar chart** (vertical) | Show ranking or ordering |

### Two Variables (Bivariate)

| Relationship | Chart | When |
|---|---|---|
| Numeric vs Numeric | **Scatter plot** | Show correlation, clusters |
| Numeric vs Numeric (large N) | **Hexbin / 2D histogram** | Too many points for scatter |
| Numeric vs Time | **Line chart** | Show trend |
| Numeric vs Category | **Box plot / Violin** (grouped) | Compare distributions |
| Numeric vs Category | **Bar chart** | Compare means or totals |
| Category vs Category | **Heatmap** | Show frequency or strength |
| Category vs Category | **Grouped bar** | Compare proportions |

### Three+ Variables (Multivariate)

| Approach | Chart | When |
|---|---|---|
| Color encoding | **Scatter + color** | 3rd variable as hue |
| Size encoding | **Bubble chart** | 3rd variable as size |
| Faceting | **Small multiples** | Compare across a categorical variable |
| Matrix | **Pair plot** | Overview of all pairwise relationships |
| Dimensionality reduction | **PCA / t-SNE scatter** | High-dimensional data |

---

## By Communication Goal

| Goal | Chart |
|---|---|
| "How is X distributed?" | Histogram, KDE, box plot |
| "How does X compare across groups?" | Bar chart, grouped box plot |
| "How does X change over time?" | Line chart, area chart |
| "Is X correlated with Y?" | Scatter plot, heatmap |
| "What makes up the whole?" | Stacked bar, treemap |
| "What's the ranking?" | Horizontal bar, lollipop |
| "Where is it geographically?" | Choropleth, scatter map |
| "What's the flow/process?" | Sankey, alluvial |

---

## Common Combinations (Compound Charts)

- **Distribution + rug plot**: Histogram with tick marks on x-axis showing individual points.
- **Scatter + marginal histograms**: `sns.jointplot()` -- shows relationship AND individual distributions.
- **Line + confidence interval**: `plt.fill_between()` -- shows uncertainty.
- **Bar + error bars**: Shows mean + standard deviation.
- **Heatmap + annotations**: Shows values in each cell of correlation matrix.
