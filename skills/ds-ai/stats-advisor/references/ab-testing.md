# A/B Testing Guide

## Sample Size Planning (Power Analysis)

Before running an A/B test, determine the required sample size:

```python
from statsmodels.stats.power import TTestIndPower, NormalIndPower, GofChisquarePower

# For means (continuous metric like revenue per user)
analysis = TTestIndPower()
n = analysis.solve_power(
    effect_size=0.2,    # Minimum detectable effect (Cohen's d)
    alpha=0.05,         # Significance level
    power=0.8,          # Statistical power (1 - beta)
    alternative='two-sided'
)

# For proportions (conversion rates)
from statsmodels.stats.proportion import proportion_effectsize
es = proportion_effectsize(0.10, 0.12)  # baseline 10%, detect 12%
analysis = NormalIndPower()
n = analysis.solve_power(effect_size=es, alpha=0.05, power=0.8)

print(f"Required sample size per group: {int(np.ceil(n))}")
```

### Rules of Thumb
- **Minimum detectable effect**: Choose the smallest effect that would be practically meaningful.
- **Power = 0.8**: Industry standard. Means 80% chance of detecting a real effect.
- **Alpha = 0.05**: Two-sided unless strong reason for one-sided.
- **Plan for 2-4 weeks** of data collection to account for weekly cycles.

---

## Running the Test

### Frequentist Approach

```python
from scipy import stats

# For conversion rates (proportions)
conversions_a, n_a = 120, 1000
conversions_b, n_b = 145, 1000

# Z-test for proportions
from statsmodels.stats.proportion import proportions_ztest
z_stat, p_value = proportions_ztest(
    [conversions_a, conversions_b],
    [n_a, n_b],
    alternative='two-sided'
)

# Confidence interval for difference
p_a, p_b = conversions_a/n_a, conversions_b/n_b
diff = p_b - p_a
se = np.sqrt(p_a*(1-p_a)/n_a + p_b*(1-p_b)/n_b)
ci_95 = (diff - 1.96*se, diff + 1.96*se)
```

### Bayesian Approach

```python
import numpy as np
from scipy import stats as sp_stats

# Beta-Binomial model for conversion rates
# Prior: Beta(1, 1) = Uniform (non-informative)
alpha_prior, beta_prior = 1, 1

# Posterior distributions
posterior_a = sp_stats.beta(alpha_prior + conversions_a, beta_prior + n_a - conversions_a)
posterior_b = sp_stats.beta(alpha_prior + conversions_b, beta_prior + n_b - conversions_b)

# Monte Carlo estimation: P(B > A)
samples_a = posterior_a.rvs(100_000)
samples_b = posterior_b.rvs(100_000)
prob_b_better = (samples_b > samples_a).mean()

# Expected lift
lift_samples = (samples_b - samples_a) / samples_a
expected_lift = lift_samples.mean()
lift_ci = np.percentile(lift_samples, [2.5, 97.5])
```

**When to prefer Bayesian:**
- Stakeholders want "probability that B is better" (more intuitive than p-values).
- Need to make decisions with small sample sizes.
- Want to incorporate prior knowledge.

---

## Common Pitfalls

### Peeking Problem
- **Don't** check results daily and stop when p < 0.05.
- **Do** pre-commit to a sample size and check once, OR use sequential testing:

```python
# Sequential testing with alpha spending
# Use the O'Brien-Fleming spending function
from statsmodels.stats.proportion import proportions_ztest
# Pre-plan interim analyses (e.g., at 50%, 75%, 100% of planned N)
# Use adjusted alpha at each look: e.g., 0.005, 0.014, 0.045
```

### Multiple Variants
- Testing A vs B vs C vs D? Apply Bonferroni: alpha_adj = 0.05 / 3 = 0.017 per comparison.
- Or use ANOVA first, then post-hoc pairwise tests.

### Simpson's Paradox
- Always check results by key segments (mobile/desktop, new/returning, geography).
- An overall positive result may hide a negative result in an important segment.

---

## Reporting Template

```markdown
## A/B Test Results: [Experiment Name]

### Setup
- **Hypothesis**: [Variant B will increase [metric] by [X]%]
- **Primary metric**: [conversion rate / revenue / engagement]
- **Test duration**: [start] to [end] ([N] days)
- **Traffic split**: [50/50]

### Sample
| Group | Users | Conversions | Rate |
|---|---|---|---|
| Control (A) | [N] | [N] | [X]% |
| Variant (B) | [N] | [N] | [X]% |

### Results
- **Relative lift**: [X]% ([CI lower]%, [CI upper]%)
- **p-value**: [value]
- **Statistical significance**: [Yes/No] at alpha = 0.05
- **Practical significance**: [Yes/No] -- [explanation]

### Decision
**[Ship / Don't ship / Run longer]** because [reasoning].

### Segment Analysis
| Segment | Lift | p-value | Note |
|---|---|---|---|
| Mobile | +5.2% | 0.02 | Significant |
| Desktop | -1.1% | 0.45 | Not significant |
```
