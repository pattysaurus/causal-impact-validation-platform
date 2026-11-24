# CIVP Walkthrough

## Modules

- `config.py` defines reproducible simulation inputs and the diagnostic thresholds used throughout the engine.
- `simulation.py` creates a panel whose treatment truth is known, plus opt-in broken scenarios for validation.
- `did.py` fits the baseline treated-by-post DiD model and returns effect, clustered uncertainty, counts, and model metadata.
- `event_study.py` estimates treated-group deviations in each period relative to `t-1`, in a chart-ready format.
- `diagnostics.py` evaluates pre-trends, a placebo date, data adequacy, control alignment, cluster count, and precision.
- `verdict.py` turns diagnostic severities into Credible, Suggestive, or Don't trust this estimate, always with a causal caveat.
- `reporting.py` combines the existing outputs into a concise clean-or-broken synthetic validation report; it adds no new estimator or diagnostic.
- `app/` provides FastAPI schemas, services, and routes that serialize engine inputs and outputs without adding statistical logic.

## Reading an analysis

Start with the DiD estimate and interval, then inspect event-study pre-period effects and diagnostics. A positive estimate is not enough: a report can be imprecise, have a poor control trajectory, lack enough clusters, or show an apparent effect before treatment. The verdict is a compact summary, not a substitute for reviewing these components.

## Questions to be able to answer

1. What known effect does the simulator plant, and where is it recorded?
2. Why does a stable unit baseline not by itself bias a DiD estimate?
3. What does the `treated × post` coefficient measure?
4. Why are unit-clustered standard errors the default?
5. Why can small cluster counts still make clustered inference unreliable?
6. Why is `t-1` the event-study reference period?
7. What would a nonzero pre-period event-study effect raise concern about?
8. Why does a non-significant pre-trend test not prove parallel trends?
9. What does a failed placebo-in-time test suggest?
10. Why does a Credible verdict still include a caveat that it cannot establish causality?
