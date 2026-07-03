# Reflection (≤1 page)

Fill this in before you submit.

**Which fault types were hardest to catch, and why?**

The missing upstream edges (`missing_upstream`) and orphaned outputs (`orphan_output`) in the `lineage` pillar were the hardest. 
Unlike the other pillars which check numerical values against static scalar bounds (like min/max thresholds for row counts, mean amount, or feature drift sigma), the lineage structure is dynamic and categorical per job. The `ctx.baseline` does not provide an expected edge count per job. I had to use `ctx.state` to dynamically build a baseline of expected upstream and downstream edge counts for each job (by observing the maximum edges seen during the stream) and flag anomalies when the actual edge count dropped below the expected maximum.

**What would you change about your cost/coverage tradeoff, if you had another pass?**

Currently, I run the toolkit inspection for every single event because the maximum penalty for `cost_overage` is capped at 20 points (`0.2 * min(cost_overage, 1)`), while the `TPR` contributes up to 50 points. A significant drop in TPR from skipping checks could easily outweigh the cost penalty. If I had another pass and faced extreme budget pressure (where events vastly exceed the budget), I would implement a probabilistic sampling strategy or stop calling tools once the penalty approaches the potential TPR gain, gracefully degrading coverage to optimize the overall score.
