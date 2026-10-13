# First-release status

Snapshot: SBLK, 9 October 2026. Built and checked locally on 12 October 2026.

| Workstream | Status |
| --- | --- |
| Reviewed SBLK fleet, source ledger and financial bridges | Implemented; estimates and source discrepancies documented. |
| Formula-driven Excel NAV, cash flow, debt, DCF and reverse valuation | Implemented with one active scenario and a native two-input sensitivity table. |
| Independent Python valuation and reconciliation | Implemented; all three cases reconcile to exported formula-calculation evidence. |
| Research report and executed notebook | Implemented; dated outputs and explicit limitations included. |
| Modular company packages and blank scaffolding | Implemented for the current dry-bulk model contract. |
| Synthetic fixture, tests, lint and type checks | Passing locally. See verification for scope. |
| GitHub Actions | Configured; inspect the actual run before claiming hosted success. |
| Peer valuation | Deferred. GNK and SB have no completed research packages. |
| Live data updates and historical forecast validation | Deferred. No operating-performance or investment-return claim. |
| Exact charter, debt and drydock schedules | Deferred pending reviewed inputs and finer scheduling modules. |
| Fleet renewal and non-dry-bulk segments | Deferred; no unfinanced replacement fleet or unsupported segment economics. |

The first release provides the reusable model and research handoff. It does not represent
every extension in the planning documents as complete. Next work should improve the
identified SBLK evidence gaps or add a properly normalized second company.
