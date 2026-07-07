# Statistical Test Selector

## Decision Tree

```
What are you comparing?
|
+-- Means / Central tendency
|   |
|   +-- How many groups?
|       +-- 1 group vs known value
|       |   +-- Normal? -> One-sample t-test
|       |   +-- Not normal? -> Wilcoxon signed-rank
|       |
|       +-- 2 groups
|       |   +-- Independent?
|       |   |   +-- Normal + equal var? -> Independent t-test
|       |   |   +-- Normal + unequal var? -> Welch's t-test (DEFAULT)
|       |   |   +-- Not normal? -> Mann-Whitney U
|       |   +-- Paired?
|       |       +-- Normal? -> Paired t-test
|       |       +-- Not normal? -> Wilcoxon signed-rank
|       |
|       +-- 3+ groups
|           +-- Independent?
|           |   +-- Normal? -> One-way ANOVA -> Tukey HSD post-hoc
|           |   +-- Not normal? -> Kruskal-Wallis -> Dunn's post-hoc
|           +-- Repeated measures?
|               +-- Normal? -> Repeated measures ANOVA
|               +-- Not normal? -> Friedman test
|
+-- Proportions
|   +-- 1 proportion vs expected -> Binomial test / Z-test
|   +-- 2 proportions -> Chi-squared / Z-test for proportions
|   +-- 3+ proportions -> Chi-squared goodness of fit
|
+-- Relationships / Associations
|   +-- Both numeric?
|   |   +-- Linear relationship? -> Pearson's r
|   |   +-- Non-linear / ordinal? -> Spearman's rho
|   +-- Both categorical? -> Chi-squared test of independence
|   +-- One numeric, one categorical? -> Point-biserial correlation (2 groups) / ANOVA (3+)
|
+-- Distributions
    +-- Does data follow distribution X? -> Shapiro-Wilk (normality), K-S test (general)
    +-- Are two distributions the same? -> K-S two-sample test
```

---

## scipy.stats Quick Reference

| Test | Function | Returns |
|---|---|---|
| Independent t-test | `ttest_ind(a, b, equal_var=False)` | t-stat, p-value |
| Paired t-test | `ttest_rel(a, b)` | t-stat, p-value |
| One-sample t-test | `ttest_1samp(a, popmean)` | t-stat, p-value |
| Mann-Whitney U | `mannwhitneyu(a, b, alternative='two-sided')` | U-stat, p-value |
| Wilcoxon signed-rank | `wilcoxon(a, b)` | stat, p-value |
| One-way ANOVA | `f_oneway(g1, g2, g3)` | F-stat, p-value |
| Kruskal-Wallis | `kruskal(g1, g2, g3)` | H-stat, p-value |
| Chi-squared | `chi2_contingency(table)` | chi2, p, dof, expected |
| Fisher's exact | `fisher_exact(table)` | odds_ratio, p-value |
| Pearson correlation | `pearsonr(x, y)` | r, p-value |
| Spearman correlation | `spearmanr(x, y)` | rho, p-value |
| Shapiro-Wilk | `shapiro(x)` | stat, p-value |
| Levene's test | `levene(a, b)` | stat, p-value |
| K-S test | `kstest(x, 'norm')` | stat, p-value |

---

## Multiple Comparisons Correction

When running multiple tests, apply correction:

```python
from statsmodels.stats.multitest import multipletests

reject, pvals_corrected, _, _ = multipletests(p_values, method='fdr_bh')
# method options: 'bonferroni', 'fdr_bh' (Benjamini-Hochberg), 'holm'
```

| Method | When to use |
|---|---|
| Bonferroni | Conservative; few comparisons (<10) |
| Holm-Bonferroni | Less conservative Bonferroni |
| Benjamini-Hochberg (FDR) | Many comparisons; controls false discovery rate |
