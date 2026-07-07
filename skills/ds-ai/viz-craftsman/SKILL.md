---
name: viz-craftsman
description: Generate publication-quality data visualizations from data and intent description. Trigger when the user asks to "plot this", "visualize", "chart this", "create a graph", "make a dashboard", "show me a heatmap/bar chart/scatter plot/histogram", "beautiful visualization", or provides data and wants to see it visually. Also triggers on "improve this chart", "make this plot better", "presentation-ready chart", or requests for specific chart types. Supports Matplotlib, Seaborn, Plotly, and Altair with Tufte-inspired design principles.
---

# Viz Craftsman

Create clean, insightful, presentation-ready visualizations.

---

## Workflow

```
1. Understand data and intent
2. Select chart type (references/chart-selector.md)
3. Generate visualization with styling rules
4. Polish and export
```

---

## Step 1 -- Understand Data and Intent

Determine:
- **Data shape**: What columns exist? Types? How many rows?
- **Message**: What insight should the chart convey?
- **Audience**: Technical (detailed) vs. executive (simplified)?
- **Medium**: Notebook, slide deck, report, social media?

If the user just says "plot this" with no specifics, default to the most informative chart for the data type.

---

## Step 2 -- Select Chart Type

Read `references/chart-selector.md` for the decision tree.

Quick reference:

| Data relationship | Chart type |
|---|---|
| Distribution (1 variable) | Histogram, KDE, box plot, violin |
| Comparison (categories) | Bar chart (horizontal for many categories), grouped bar |
| Relationship (2 numeric) | Scatter plot, hexbin for large N |
| Trend over time | Line chart, area chart |
| Composition (parts of whole) | Stacked bar, treemap (NOT pie charts) |
| Correlation matrix | Heatmap with annotated values |
| Geographic | Choropleth, scatter on map |
| Ranking | Horizontal bar, lollipop chart |
| Flow / hierarchy | Sankey, treemap |

---

## Step 3 -- Generate Visualization

### Default Styling Rules (apply to EVERY chart)

```python
import matplotlib.pyplot as plt
import matplotlib as mpl

# Apply to all charts
plt.rcParams.update({
    "figure.figsize": (10, 6),
    "figure.dpi": 150,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "font.size": 12,
    "axes.titlesize": 16,
    "axes.titleweight": "bold",
    "axes.labelsize": 13,
})
```

### Color Palettes

| Purpose | Palette | Code |
|---|---|---|
| Categorical (<=6) | Custom muted | `["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860"]` |
| Categorical (>6) | `tab20` | `plt.cm.tab20` |
| Sequential | `viridis` or `Blues` | `cmap="viridis"` |
| Diverging | `RdBu_r` | `cmap="RdBu_r"` |
| Accessible | `colorblind` from seaborn | `sns.color_palette("colorblind")` |

**Default to colorblind-friendly palettes.**

### Must-Have Elements

Every chart MUST include:
1. **Title**: Descriptive, states the insight (not just "Bar Chart of X").
   - Good: "Revenue grew 3x in Q4, driven by enterprise segment"
   - Bad: "Revenue by Quarter"
2. **Axis labels**: With units where applicable.
3. **No clutter**: Remove unnecessary gridlines, borders, legends when obvious.
4. **Data labels**: On bar charts with few bars (<8). On line charts at key inflection points.
5. **Source annotation**: `plt.figtext(0.99, 0.01, "Source: ...", ha="right", fontsize=8, color="gray")` when data source is known.

### Anti-Patterns (NEVER do these)

- Pie charts (use horizontal bar instead).
- 3D charts (distorts perception).
- Dual y-axes (use two panels instead).
- Rainbow color schemes (not accessible).
- Truncated y-axes without clear indication.
- Excessive grid lines or chart junk.

---

## Step 4 -- Polish and Export

### For Notebooks
```python
plt.tight_layout()
plt.show()
```

### For Files
```python
plt.savefig("chart_name.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.savefig("chart_name.svg", bbox_inches="tight", facecolor="white")  # Vector format
```

### For Plotly (Interactive)
```python
fig.update_layout(
    template="plotly_white",
    title=dict(text="Title", font=dict(size=20)),
    font=dict(size=14),
    margin=dict(l=60, r=30, t=60, b=50),
    showlegend=True,
)
fig.write_html("chart_name.html")
```

---

## Library Selection

| Scenario | Library |
|---|---|
| Static charts for reports/papers | Matplotlib + Seaborn |
| Interactive exploration in notebooks | Plotly Express |
| Dashboards | Plotly Dash or Streamlit |
| Complex statistical plots | Seaborn |
| Declarative/grammar-of-graphics style | Altair |

Default: **Matplotlib + Seaborn** unless interactivity is needed or requested.
