# Methodology

## Purpose

CIVP is a decision-support project for a simple, single-intervention Difference-in-Differences (DiD) design. Its output can be consistent with an intervention effect, raise concern about an estimate, or indicate insufficient evidence. It cannot establish causality by itself.

## Synthetic data-generating process

For unit `i` in period `t`, the synthetic outcome is:

```text
Y_it = unit_baseline_i + common_time_trend × t
     + treated_pretrend_i,t + fake_pre_effect_i,t
     + treatment_effect × treated_i × post_t + noise_it
```

`unit_baseline` creates stable differences between units. A shared time trend affects both groups. By default, `treated_pretrend` and `fake_pre_effect` are zero, so the simulated untreated trends are parallel. The real planted effect is added only for treated units at and after the shared intervention date. Every simulation uses a local, fixed-seed random generator.

Optional failure modes are deliberately explicit:

- `pre_trend_difference` changes the treated group's pre-treatment slope.
- `fake_pre_treatment_effect` adds a treated-only shift in the latter half of the pre-period.
- `missing_data_rate` deterministically turns a share of outcomes into missing values.

## Baseline DiD

The fitted model is:

```text
outcome = β0 + β1·treated + β2·post + β3·(treated × post) + error
```

`β3` is the treated group's post-period change minus the control group's post-period change. It is the estimated average intervention effect in this model. The estimator uses statsmodels OLS with unit-clustered standard errors by default. Non-clustered OLS errors remain available for comparison and are explicitly labelled as such.

Clustered errors allow observations within the same unit to be correlated over time. They are still unreliable with few independent units; the platform reports the cluster count and later warns below 30 clusters, with a serious concern below 10 effective clusters.

## Recovery validation

The DiD tests run 200 fixed-seed simulations with 20 treated and 20 control units. The clustered 95% interval must cover the known planted effect in at least 90% of runs. The mean estimate must be within 1.0 outcome unit (5% of the planted 20-unit effect) of truth. This is a synthetic calibration check, not evidence that the estimator will be valid for a real intervention.

With the current fixed seeds and package versions, observed clustered-interval coverage is 94.5% (189 of 200 runs).

## Event study

The event-study model adds treatment-by-relative-time interactions while controlling for common relative-time indicators. The period immediately before the intervention (`t-1`) is omitted and displayed as a zero reference point. Output contains x-values, estimates, 95% bounds, labels, period types, and zero-line metadata for charting. Pre-period coefficients are kept distinct from post-period effects.

## Diagnostic logic and thresholds

Thresholds live in `DiagnosticThresholds` so they can be inspected and changed deliberately.

| Check | Decision rule | Interpretation |
| --- | --- | --- |
| Pre-trend | Treated-by-time pre-period p-value below 0.05 | Raises concern about parallel trends. A non-significant test does not prove parallel trends. |
| Placebo in time | Artificial pre-period intervention p-value below 0.05 | Raises concern about an early treated-group deviation. |
| Data adequacy | Fewer than 5 units in either group, no usable pre/post data, over 5% missing cells, or fewer than 10 effective clusters | Serious insufficiency. |
| Control quality | Pre-period correlation below 0.90 or slope difference above 0.50 | Raises concern that the control trajectory is not a close comparison. |
| Small clusters | Under 30 clusters warns; under 10 is serious | Cluster-robust inference may be unreliable. |
| Precision/power | 95% CI half-width above 10.0 or interval includes zero | Insufficient precision for the project's 20-unit reference effect. MDE is `1.96 × clustered SE`. |

The thresholds organize caution; they do not validate a causal claim. Diagnostics are designed to identify evidence that is consistent with problems, not to prove assumptions true.

## Verdicts

Any serious diagnostic produces **Don't trust this estimate**. Warning-only reports produce **Suggestive**. An all-info report produces **Credible**. Every verdict includes the same caveat: passing checks is consistent with the minimum configured assumptions but cannot establish causality.
