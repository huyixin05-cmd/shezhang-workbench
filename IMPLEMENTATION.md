# Implementation record

Plan: ../docs/superpowers/plans/2026-10-01-teach-agent-first-release.md
Spec: ../docs/superpowers/specs/2026-10-01-teaching-agent-design.md

Ruling: proceed inline with the user-approved requirements without another permission round. New standalone repository because no existing product Git checkout exists; historical files are unchanged. Cost: future integration is a separate decision.
Ruling: use native Windows commands and this persistent ledger instead of Bash-only task scripts. Cost: less automated ledger bookkeeping; verification commands and outcomes are recorded below.

Pre-flight: Store supplies plan revisions/job snapshots to service; browser and MCP share API; renderer/export use UUID-owned files. No arbitrary model Python execution.

Task 1 complete: approval/stale revision/immutable versions/restart tests, initial RED then GREEN.
Task 2 complete: malformed JSON, embedded resources and remote-reference rejection; 213 components and all KaTeX fonts. Browser regression reproduced static instrument reading, then upstream runtime remount integration fixed it.
Task 3 implemented: authenticated loopback API, editable plan UI, jobs/revisions, bounded checks/repair, cancellation. Stale approval and model-review contradictions tested. UI walkthrough ongoing.
Task 4 implemented: controlled Manim template, actual 12-second 1280x720 H.264 render, first-frame and 10-second frame inspection; real MP4 import/combined export tests. Official MCP 2.2 initialize/list tools/confirmation-rejection passed. WorkBuddy UI unverified.
Task 5 in progress: launchers, packaging, docs and CI definition written. Final fresh review and distribution verification pending.

2026-10-01: full local suite 34 passed in 4.92s. Live model unavailable (no credentials/configuration); model-boundary fixtures are tests only. No claim of live generation quality or speed. macOS/Linux and a second physical computer unverified.

Ruling: pin current official MCP SDK 2.2 and use its MCPServer and snake_case result fields, established from installed source. Cost: older SDKs require adaptation.
Ruling: combined versions retain the source interactive version and require editing that version then reattaching video. Editable ZIP contains source, not a project-import feature. Cost: an extra attachment step until richer editing is implemented.
Ruling: preserve the standalone branch and source distribution for local iteration; no remote destination/account is configured yet. No GitHub publication claim.


Final verification: 45 tests passed in 5.53s; 4 Manim label-boundary cases passed. Real ZIP downloaded through UI and relocated/extracted to a new Chinese directory; isolated browser verified interaction and local MP4 loading. Editable install and wheel build passed. See VERIFICATION.md for explicit fixture/live boundaries.

Final review: fresh read-only reviewer on whole first-release code (f10e648). Four important findings accepted and fixed in one pass; no deferred minor findings.
Final: fixed CSP placement bypass — four malicious-prefix regression cases RED→GREEN.
Final: fixed outdated revision enqueue — test_revision_enqueue_rechecks_approval_and_base_version RED→GREEN.
Final: fixed inaccessible prior versions — reproduced in actual UI, added independent entry, verified current plan remains unconfirmed while existing output opens.
Final: fixed clipped animation labels — tests/check_manim_layout.py RED→GREEN, rendered edge case inspected.
Final: fixed blank iframe after visibility lifecycle — actual iframe body had zero dimensions; fresh sandboxed frame shows real content and nonzero dimensions.
Final: fixed file transfer compatibility — scoped file access test RED→GREEN, actual browser ZIP download and isolated offline video loading verified.

Ruling: restrict HTML to an unambiguous doctype/html/head prefix rather than trying to repair every malformed document. Cost: unusual but harmless model HTML may require regeneration.
Ruling: use one-hour random capabilities scoped to one version for local media/downloads. No management token in URLs; host remains loopback-only. Cost: preview must be reopened after expiry; holders of a file link can read only that version during its lifetime.
Final: Ruling: live-model quality/latency, WorkBuddy client, other systems/physical computers and all-component quality require future environments/fixtures. These are explicitly unverified; shipping a preview does not certify them. Cost: compatibility and pedagogical quality still need real-world acceptance.
Final: Ruling: unsupported arbitrary animation themes, direct combined-version editing and project re-import remain documented first-release boundaries. Cost: additional local workflow steps for those cases.

Tasks 1–5 implemented and verified within the preview boundary. Remote publishing not performed. The local branch is retained; no other checkout or worktree was deleted.

Distribution check caught root dist/ ignore rule excluding vendored KaTeX dist from Git. Anchored output-directory ignores, added source-integrity regression and verified all 710 upstream files in the Git index. Final suite now 46 tests.

Teaching design update: integrated selected pinned html-anything prompt sections. Added request/difficulty/reason/teaching-response analysis and sequenced explanation/actions; no student-evidence prerequisite. Added bounded separate planning review, editable sequence UI and provenance in reports. 51 tests pass; fixed-response browser editing/reordering/persistence verified. Live model quality remains unverified.


Animation workflow update (supersedes first-release template-only boundary): native pinned Sol stages/client/validators integrated with teacher-approved general storyboards. Existing local VideoScene and text checker reused; product owns render/frame-review/repair/final/export orchestration. New plans reject legacy templates; stored templates remain readable. Animation revisions and explicit editable export allowlist added.
Ruling: preserve Sol's native Codex CLI/ChatGPT authentication instead of silently routing through the HTTP model. Cost: separate local CLI login; currently missing, so live generation quality remains unverified.
Ruling: execute generated scenes locally after static checks, with sanitized environment and owned artifact paths; these are not an OS sandbox. Document this change from the first-release fixed-template execution boundary.
Real renderer test: manually authored non-force geometry scene, 16:9 and 9:16, both final 720p H.264 ~6s; inspected PNG evidence. Fixed render-config frame dimensions after real vertical inspection showed overly small content. No live model claim.

Final animation review: 3 important findings fixed in one pass with regressions. Editable export includes validation.json. Static guard rejects dangerous identifier aliases/import members and renderer-config access. Product CLI adapter retains native command/auth/stage contracts but uses owned process trees instead of upstream parent-only kill/unbounded reader joins. Windows Job Objects (kill-on-close) and POSIX groups own descendants even after parent exit. 69 tests passed; real Manim preview succeeded after lifecycle changes. Upstream source hashes unchanged.
