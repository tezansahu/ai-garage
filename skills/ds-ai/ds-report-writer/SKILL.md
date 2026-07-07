---
name: ds-report-writer
description: Generate structured, stakeholder-ready data science reports from analysis results, notebooks, metrics, and charts. Trigger when the user asks to "write a report", "summarize my analysis", "create a findings document", "executive summary", "write up results", "document this analysis", "stakeholder report", "present findings", or has completed an analysis and needs to communicate results. Also triggers on "make this notebook into a report", "explain these results to non-technical audience", or "prepare a slide-ready summary".
---

# DS Report Writer

Transform analysis outputs into clear, compelling reports for technical and non-technical audiences.

---

## Workflow

```
1. Gather analysis artifacts (notebooks, metrics, charts, data)
2. Determine audience and format
3. Generate report using appropriate template
4. Polish language and structure
```

---

## Step 1 -- Gather Artifacts

Collect from the user's workspace:
- Notebook outputs (`.ipynb` cell outputs)
- Saved charts (`.png`, `.svg`)
- Metrics / results (printed outputs, CSV files)
- Model comparison tables
- Feature importance rankings

---

## Step 2 -- Audience and Format

| Audience | Tone | Technical depth | Length |
|---|---|---|---|
| Executive / Business | Action-oriented, business impact | Minimal -- no code, few stats | 1-2 pages |
| Technical stakeholder (PM, analyst) | Balanced insights + methodology | Moderate -- key stats, no code | 2-4 pages |
| Technical peer (DS/ML engineer) | Precise, reproducible | Full -- code snippets, formulas, configs | 4-8 pages |

### Output Format

| Request | Format |
|---|---|
| "Report" / "document" | Markdown (`.md`) |
| "Slide deck" / "presentation" | Delegate to `pptx` skill if available, else markdown with slide-break markers |
| "Email summary" | Short markdown with copy-paste-ready text |

---

## Step 3 -- Generate Report

### Executive Report Template

```markdown
# [Project Title]: Key Findings

**Date**: [date] | **Author**: [name] | **Status**: [Draft/Final]

---

## Bottom Line

[1-2 sentences: what did you find and what should we do about it?]

## Key Findings

1. **[Finding]**: [1-2 sentences with the key metric and business implication]
2. **[Finding]**: [...]
3. **[Finding]**: [...]

## Recommendation

[What action should be taken? By whom? By when?]

## Methodology (Brief)

[2-3 sentences: what data was used, what approach was taken, key assumptions]

## Next Steps

- [ ] [Action item 1]
- [ ] [Action item 2]

---
*For detailed methodology, see the [technical appendix](link).*
```

### Technical Report Template

```markdown
# [Project Title]

**Date**: [date] | **Author**: [name]

---

## 1. Objective

[What question were we trying to answer? What problem were we solving?]

## 2. Data

- **Source**: [where the data came from]
- **Size**: [rows x columns]
- **Time range**: [if applicable]
- **Key variables**: [target + top features]
- **Data quality notes**: [missing values, cleaning applied]

## 3. Methodology

### Approach
[Description of the analytical approach]

### Models Evaluated
[If applicable: table of models with hyperparameters]

### Evaluation Metric
[Why this metric was chosen]

## 4. Results

### Key Metrics
| Metric | Value |
|---|---|
| [Primary metric] | [value] |
| [Secondary metric] | [value] |

### Visualizations
[Embed or reference key charts]

### Feature Importance
[Top features and their contribution]

## 5. Discussion

- **What worked**: [...]
- **Limitations**: [...]
- **Caveats**: [...]

## 6. Recommendations

1. [Actionable recommendation with expected impact]
2. [...]

## 7. Next Steps

- [ ] [Follow-up analysis]
- [ ] [Deployment plan]
- [ ] [Monitoring approach]

## Appendix

### A. Data Dictionary
| Column | Type | Description |
|---|---|---|

### B. Detailed Results
[Additional tables, charts, model configs]
```

---

## Step 4 -- Polish

### Writing Principles
- **Lead with the "so what"**: Every section starts with the conclusion, then supports it.
- **Quantify claims**: "Revenue increased" -> "Revenue increased 23% ($1.2M) QoQ."
- **Active voice**: "The model achieved 94% accuracy" not "94% accuracy was achieved."
- **No jargon for non-technical readers**: "The model correctly identifies 94 out of 100 cases" not "The model has 94% accuracy with 0.91 F1 score."
- **Consistent tense**: Past tense for what was done, present for findings that still hold.
- **Meaningful chart titles**: State the insight, not the chart type.

### Checklist Before Delivery
- [ ] Executive summary can stand alone
- [ ] All claims have supporting data
- [ ] Charts are referenced in text
- [ ] Limitations are honestly stated
- [ ] Next steps are specific and actionable
- [ ] Spell-checked, no orphan headings
