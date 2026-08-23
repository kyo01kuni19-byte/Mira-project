# Master Profile Extraction Pilot v0.1

## Purpose

Extract Kuni Master Profile information into the Unified Learning Database without summarizing or replacing the source document.

The objective is decomposition into reusable Knowledge Entities while preserving Origin.

---

# Extraction Principle

Master Profile is treated as a Source Container.

It may contain multiple Entity Content Types:

- Value
- Principle
- Capability
- Practice
- Architecture
- Learning
- Decision
- Project-related knowledge

Content Type is not the hierarchy.

---

# Unified Entity Structure

Each extracted Entity should be represented by:

## Hierarchy
Where the Entity exists in value / knowledge / application scope.

## Object
What the Entity is about.

## Purpose
Why the Entity exists.

## State
Current maturity or recognition status.

## Relationship
Current connection to other Entities.

## Formation / Evolution Trace
How the Entity originated and changed.

## Evidence
Supporting source or validation information.

---

# Initial Extraction Targets

## Core Architecture

Expected Content Type:
Capability / Architecture Candidate

Extraction focus:

- What capability is described?
- What value creation process does it support?
- What other Entities depend on it?

---

## Value Creation Principles

Expected Content Type:
Value / Principle Candidate

Extraction focus:

- What value is intended?
- What principle enables that value?
- What capability is generated from the principle?

---

## Practice and Application Examples

Expected Content Type:
Practice / Application Knowledge

Extraction focus:

- How is the principle applied?
- In what context is it validated?
- What boundary conditions exist?

---

# Validation Rule

Do not create new structure unless existing Knowledge Entity structure cannot represent the information.

The purpose of this pilot is to test whether Master Profile information can be decomposed consistently into the Unified Learning Database.
