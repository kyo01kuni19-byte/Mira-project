# Change Control Agent Prototype

Minimal executable slice implementing the working governance contracts agreed in the Change Control Agent Development Baseline.

Implemented:
- explicit Core/Matrix baseline resolution
- DRAFT / FORMAL_REQUEST / APPROVED state boundary
- Formal Submission freeze fingerprint (+/ optional artifact SHA-256)
- explicit Owner precedence + A/R/C/I preservation
- Purpose traversal from Field_Purpose_Catalog and actual Matrix row values
- Human CCS completeness + Overall CCS = MAX
B - Human/Agent CCS difference-reason control helper

Not implemented:
- production repository / identity / authorization
- formal approval execution
- SAP writes
- complete assessment rule engine
- production audit trail

The runtime is intentionally analysis-first and authority-limited.
