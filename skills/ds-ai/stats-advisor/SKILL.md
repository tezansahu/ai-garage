---
name: stats-advisor
description: Recommend and execute the right statistical test for a given question, with plain-English interpretation. Trigger when the user asks about "A/B test", "hypothesis test", "statistical significance", "p-value", "confidence interval", "is this difference significant", "compare two groups", "correlation test", "chi-squared", "t-test", "ANOVA", "power analysis", "sample size", "Bayesian vs frequentist", "statistical test", "effect size", or any question about whether an observed difference is real or due to chance. Also triggers on "which test should I use" or "analyze this experiment".
---

# Stats Advisor

Recommend, execute, and interpret the right statistical test with clear, honest communication.

---

## Workflow

```
1. Understand the question
2. Select the appropriate test (references/test-selector.md)
3. Check assumptions
4. Execute test
5. Interpret and report results
```

---

## Step 1 -- Understand the Question

Determine:
- **What is being compared?** (means, proportions, distributions, relationships)
- **How many groups?** (1, 2, 3+)
- **Paired or independent?** (same subjects measured twice vs. different groups)
- **Sample size?** (affects test choice and power)
- **What is the practical question?** (not just "is p < 0.05" but "should we ship this?")

---

## Step 2 -- Select Test

Read `references/test-selector.md` for the full decision tree.

Quick reference:

| Question | Test |
|---|---|
| Two means, independent groups | Independent t-test (or Welch's t-test) |
| Two means, paired/matched | Paired t-test |
| Two proportions | Chi-squared test or Z-test for proportions |
| Two distributions | Mann-Whitney U (non-parametric) |
| Three+ group means | One-way ANOVA (+ Tukey post-hoc) |
| Three+ group distributions | Kruskal-Wallis |
| Correlation (linear) | Pearson's r |
| Correlation (ordinal/non-linear) | Spearman's rho |
| Association (categorical) | Chi-squared test of independence |
| One proportion vs expected | Binomial test |
| Normality check | Shapiro-Wilk test |
| Variance equality | Levene's test |

---

## Step 3 -- Check Assumptions

Before running any test, verify its assumptions:

### For Parametric Tests (t-test, ANOVA)
1. **Normality**: Shapiro-Wilk test or visual QQ plot. If p < 0.05, consider non-parametric alternative.
2. **Equal variances**: Levene's test. If violated, use Welch's t-test.
3. **Independence**: Observations must be independent (study design, not a test).
4. **Sample size**: n >= 30 per group for Central Limit Theorem to help.

### For Chi-Squared
1. **Expected frequency**: All expected cell counts >= 5. If not, use Fisher's exact test.
2. **Independence**: Observations are independent.

If assumptions are violated, recommend the non-parametric alternative and explain why.

---

## Step 4 -- Execute Test

### Standard Implementation Pattern

```python
from scipy import stats
import numpy as np

# Example: Independent t-test
t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False)  # Welch's by default

# Effect size (Cohen's d)
cohens_d = (np.mean(group_a) - np.mean(group_b)) / np.sqrt(
    (np.std(group_a, ddof=1)**2 + np.std(group_b, ddof=1)**2) / 2
)

# Confidence interval for difference of means
from scipy.stats import sem
diff = np.mean(group_a) - np.mean(group_b)
se_diff = np.sqrt(sem(group_a)**2 + sem(group_b)**2)
ci_95 = (diff - 1.96 * se_diff, diff + 1.96 * se_diff)
```

**Always compute and report:**
1. Test statistic
2. p-value
3. Effect size (Cohen's d, Cramer's V, etc.)
4. Confidence interval

---

## Step 5 -- Interpret and Report

### Interpretation Template

```markdown
## Statistical Analysis: [Question]

### Setup
- **Groups**: [Group A] (n=[N]) vs [Group B] (n=[N])
- **Test**: [Test name]
- **Significance level**: alpha = 0.05

### Results
- **[Group A] mean**: [value] (SD = [value])
- **[Group B] mean**: [value] (SD = [value])
- **Difference**: [value] ([CI lower], [CI upper])
- **Test statistic**: [name] = [value]
- **p-value**: [value]
- **Effect size**: [name] = [value] ([interpretation: small/medium/large])

### Interpretation
[Plain-English explanation: what this means for the user's actual question]

### Recommendation
[What should be done based on these results?]

### Caveats
- [Any assumption violations]
- [Sample size concerns]
- [Multiple comparisons issue if applicable]
```

### Effect Size Interpretation

| Measure | Small | Medium | Large |
|---|---|---|---|
| Cohen's d | 0.2 | 0.5 | 0.8 |
| Pearson's r | 0.1 | 0.3 | 0.5 |
| Cramer's V (df=1) | 0.1 | 0.3 | 0.5 |
| Eta-squared | 0.01 | 0.06 | 0.14 |

### Honest Reporting Principles

- **Report effect sizes, not just p-values.** A p < 0.001 with Cohen's d = 0.05 is statistically significant but practically meaningless.
- **Report confidence intervals.** They convey both significance and effect magnitude.
- **Distinguish statistical and practical significance.** "The difference is statistically significant (p = 0.03), but the effect is small (d = 0.15), meaning the practical impact is minimal."
- **Flag multiple comparisons.** If running multiple tests, apply Bonferroni or FDR correction.
- **Never say "the results prove..."** Statistics provide evidence, not proof.

---

## A/B Test Specifics

For A/B test analysis, also read `references/ab-testing.md` which covers:
- Sample size planning (power analysis)
- Sequential testing and peeking problems
- Multiple variant testing
- Practical significance thresholds
- Bayesian A/B testing alternative
