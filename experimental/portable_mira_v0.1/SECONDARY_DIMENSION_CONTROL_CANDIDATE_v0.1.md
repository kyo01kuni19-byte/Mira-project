# Secondary Dimension Activation Discipline Candidate v0.1

**Status:** EXPERIMENTAL CONTROL CANDIDATE — NOT APPROVED

## Evidence Basis

The three-case true-holdout synthesis records secondary-dimension inflation in
all three reviewed cases. It classifies an experimental activation-discipline
change as `CHANGE_JUSTIFIED_NOW`, with medium overfitting risk. No deterministic
Runtime mis-traversal was observed, and three cases do not establish a general
failure or general capability.

## Value Intent

Reduce unnecessary semantic activation without omitting dimensions that are
materially necessary to understand the problem, preserve a decision boundary,
or support deterministic Runtime handoff.

## Candidate Control

`possible_secondary_dimensions` remains observational under the unchanged
Semantic Judgment Contract v0.1a. The OpenAI adapter request now carries an
explicit, versioned policy:

- include a dimension only when omission would materially impair problem
  understanding, a decision boundary, or deterministic Runtime handoff;
- do not include a dimension merely because it is mentioned, plausible,
  contextually related, or potentially useful;
- preserve every dimension that crosses that threshold, and emit an empty list
  when none does;
- do not use secondary dimensions to select edges, direct traversal, authorize
  action, or require Human escalation.

The adapter is identified as `openai.semantic_judgment.v0.2-candidate`. The
contract schema, deterministic Runtime, routing registry, historical evidence,
and frozen evaluations are unchanged.

## Deterministic Verification Boundary

Local tests can verify request construction, policy version observability,
contract compatibility, and the existing counter-failure evaluator's ability
to detect both inflation and material omission. They cannot establish that a
provider follows the policy or that semantic quality improves.

## Next Evaluation

Use new development cases, or separately authorized sealed cases, to compare
the candidate against the prior adapter behavior. Evaluate both:

- reduction in unsupported secondary dimensions; and
- preservation of all materially required secondary dimensions.

Do not rewrite or replay the three frozen holdout results as if they were
candidate-control evidence. Do not promote this candidate without behavioral
evidence and Human/MIRA review.
