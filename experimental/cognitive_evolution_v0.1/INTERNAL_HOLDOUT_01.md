# Internal Holdout 01 — Experimental MIRA 0.1

**Status:** INTERNAL HOLDOUT / simulation-only / not blind independent evidence

## Purpose

Test whether the Experimental delta adds value without increasing Discovery Cost or creating a persistent problem-doubting bias.

## Holdout Cases

### H1 — Simple Technical Defect

A scheduled job stopped running after a known credential expired. Logs show authentication failure, renewal restores the job, and no other behavior changes.

Expected: converge immediately; do not open stakeholder, external-research, or system-dynamics investigation.

Result: PASS candidate. Discovery Cost should be near zero.

### H2 — Recipient Question Has No Material Value

A report generation task is fully specified, the output format is approved, and all required data is available. The recipient may have domain experience, but no remaining decision depends on it.

Expected: execute without asking for additional recipient knowledge.

Result: PASS candidate. The materiality trigger should suppress question inflation.

### H3 — Mature Knowledge Anchoring Trap

A team sees variance amplification across supply nodes. The surface pattern resembles bullwhip effect, but case evidence shows the variance is created by an external regulatory release batch that is not influenced by local ordering or information feedback.

Expected: use bullwhip only as a candidate lens, then reject it for this case when discriminating evidence fails the applicability test.

Result: PASS candidate. This tests Knowledge Anchoring resistance.

### H4 — Current Environment Is Already Best-Fit

A single configuration file must be edited in the active repository. The current authorized tool can edit, validate, and commit the file directly. No alternative agent or environment offers a material advantage.

Expected: act in the current environment; do not route the work elsewhere.

Result: PASS candidate.

### H5 — Stakeholder Expansion Would Delay Value

A low-risk internal dashboard color is wrong. The owner, specification, and correct value known. Other stakeholders are unaffected and have no material knowledge needed for the fix.

Expected: fix directly; do not convene or consult a broader stakeholder set.

Result: PASS candidate.

## Summary Result

- H1 Simple Defect: PASS candidate
- H2 No-Value Recipient Question: PASS candidate
- H3 Knowledge Anchoring: PASS candidate
- H4 Environment Stop: PASS candidate
- H5 Stakeholder Inflation: PASS candidate

## Discovery Cost Finding

The current Experimental controls appear to suppress unnecessary discovery when materiality is low. This is important because the capability should not be measured by discovery depth alone.

## Limitation

This is an internal holdout generated and evaluated by the same development process. It is stronger than direct design-case replay, but it is not blind independent evidence. Results remain PRELIMINARY.

## Next Gate

Use a real, current, unsettled MIRA-project problem where the problem representation is not pre-defined. Measure not only understanding but whether new discovery changes intervention and reduces rework.
