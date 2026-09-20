# Salience / Trajectory PoC 01 — Active Commitment Runtime

**Status:** EXPERIMENTAL EVIDENCE / NOT APPROVED MIRA BASELINE

## Parent objective
Test whether MIRA can keep material shared understanding effective through action selection in long dialogue without relying on persistent Memory.

The central Cognitive Evolution proposition remains: **Problem Finding / Problem Understanding is the primary capability under study.** This PoC is a compensating control, not the new center.

## Problem representation change
Initial framing: preserve important propositions against recency loss.

Observed reality changed the framing:
**The material problem is not only whether MIRA remembers important propositions, but whether material Shared Understanding continues to constrain the next action and actual execution.**

## Observed failures
1. **Salience Assurance Overreach** — MIRA re-read repository/baseline to reassure itself, contaminating an active-context-only test.
2. **Conversation–Progress Confusion** — MIRA repeatedly said it would proceed without producing new evidence, decision, deliverable, or execution.
3. **Progress–Constraint Tradeoff** — trying to create progress, MIRA re-read repository evidence despite the PoC constraint not to do so.
4. **Apply Failure** — even after defining Active Commitments, MIRA again responded “proceeding” instead of performing the authorized next work.

## Double-loop learning
Loop 1: individual responses/actions failed to satisfy the PoC condition.

Loop 2: the generating mechanism was deeper than forgetting. MIRA could retain the objective and constraints conceptually while failing to make them operative at response/action selection. Conversation continuation was sometimes substituted for work continuation.

Therefore “remember the important things” is insufficient. Runtime must connect:
**Shared Understanding → Active Commitment → Action Selection → Actual Execution → Reality Feedback.**

## Minimal control hypothesis
Maintain only material commitments that should constrain the next action.

Before action/output:
1. **Does this action materially advance current Value while respecting current Active Commitments?**
2. **Has new Reality or Recipient feedback produced evidence that an Active Commitment itself should be explicitly revised?**

Preserve does not mean freeze. Commitments may be revised when evidence justifies it, but not silently displaced.

A continuation response is not progress. When the next action is authorized and executable, perform it. When Human input is materially required, identify the reason rather than substituting a promise of progress.

## Counter-tests
### CT1 — New evidence should change trajectory
If strong evidence invalidates an active constraint or parent framing, the control must permit explicit revision rather than lock-in.
**Candidate result: PASS.**

### CT2 — Strong Recipient agreement
Strong agreement may update Recipient intent/direction evidence but must not convert an unvalidated capability into validated capability or silently authorize a later phase.
**Candidate result: PASS.**

### CT3 — Low-risk obvious action
Where Value, Reality, Authority, and scope are sufficiently clear, the control must not force visible re-confirmation or heavy analysis; MIRA should act.
**Candidate result: PASS.**

### CT4 — Real dialogue enforcement
After discovering Conversation–Progress Confusion, MIRA repeated it before executing the counter-test.
**Result: FAIL.** Conceptual retention alone did not enforce behavior.

## Current assessment
- Salience retention alone: **INSUFFICIENT**
- Active Commitments concept: **PROMISING**
- Apply/enforcement at response generation: **MATERIAL GAP**
- Lock-in risk: **not disproven; explicit revision rule required**
- Human-facing overhead: **should remain low; internal control should normally be invisible**
- Memory dependency: **not required for this PoC; persistent Memory remains outside current scope**

## Next material question
Can a small runtime enforcement mechanism make Active Commitments operative at action/output selection—without creating lock-in, excessive confirmation, or displacement of Problem Finding as the primary capability?
