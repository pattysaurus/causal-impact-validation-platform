# Delhi Odd-Even / CPCB Case-Study Protocol

This is a later, deliberately difficult demonstration—not a pre-committed causal claim.

## Before modeling

1. Record the exact intervention date and policy phases.
2. Document CPCB source URLs, extraction dates, pollutant definition, units, station coverage, and cleaning decisions.
3. Define a treated geography and a defensible control geography before inspecting estimates.
4. Check for staggered policy timing, spillovers, weather, holiday, seasonal, and concurrent-policy confounding.

## Source-discovery record

The official CPCB January 2016 Odd-Even assessment identifies the intervention window as 1–15 January 2016 and describes its use of eight operational continuous monitoring stations. It is contextual material, not a ready-to-model panel or a causal conclusion. The CPCB Central Control Room links its CAAQMS data repository and station lists. Record the exact query, downloaded files, access date, and any revisions before placing a copy in `data/raw/`.

- CPCB Odd-Even assessment: <https://cpcb.nic.in/OddEvenScheme-Jan.pdf>
- CPCB Central Control Room / CAAQMS repository: <https://app.cpcbccr.com/ccr>

No CPCB data have been downloaded, cleaned, or modeled in this repository yet.

## Required platform checks

Run the same DiD, event-study, data-adequacy, control-quality, small-cluster, placebo, and precision checks used for synthetic validation. Preserve the raw data separately and record all exclusions.

## Interpretation

A passing diagnostic report is only consistent with the chosen design assumptions. It cannot establish causality. The expected acceptable outcome is **Don't trust this estimate** when timing, controls, clusters, or precision are inadequate.
