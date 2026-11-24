# Project Scope and Limitations

- Supports one intervention date, one treated group, binary treatment, and balanced or near-balanced panels.
- Staggered adoption and heterogeneous treatment timing are out of scope because basic two-way fixed-effects DiD may be biased in those settings.
- The current event-study design assumes a shared intervention date; it is not an estimator for staggered timing.
- The baseline estimator uses unit-clustered standard errors, but small numbers of clusters make conventional clustered standard errors unreliable. The platform warns below 30 clusters and raises a serious concern below 10 effective clusters.
- Passing a pre-trend, placebo, adequacy, control-quality, cluster, or precision check does not establish causality. In particular, a non-significant pre-trend test does not prove parallel trends.
- The diagnostics cannot rule out confounding, spillovers, anticipation outside the modeled fake-effect check, measurement error, changes in composition, or unrelated concurrent interventions.
- Synthetic recovery tests validate behavior under the platform's own known data-generating process; they do not validate a real-world causal design.
- No authentication, accounts, payments, or multi-user collaboration are included in the MVP.
- The Delhi Odd-Even case study is a later, deliberately difficult real-world demonstration and may legitimately return “Don’t trust this estimate.”
