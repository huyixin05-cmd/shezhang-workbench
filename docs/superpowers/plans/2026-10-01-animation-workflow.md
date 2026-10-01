# Manim workflow integration

> For agentic workers: use superpowers:executing-plans. Implement inline, followed by one fresh-context review.

**Goal:** Replace the topic-specific animation entry with the existing Sol staged scene-generation workflow, preserving one teacher approval and local portable outputs.

**Spec:** The user requests reuse of the local Manim workflow, not an expanding catalog of fixed topic templates. Teacher intent, teaching order and storyboard are prepared automatically, confirmed once, then rendered and checked without intermediate approvals. Keep the homepage simple.

**Architecture:** Preserve a pinned copy of the existing native Sol stages/client/validators and their license. A product worker supplies the approved lesson as the binding brief; the existing Sol stages generate a new scene. The worker owns static checks, low-quality render, PyAV frame extraction, visual review/repair, and final 720p render/review. Use the existing Manim environment; Sol retains its Codex CLI login backend. No HTTP-provider substitution inside Sol. Old force-composition plans stay executable as legacy artifacts.

**Constraints:** Do not alter the source Math-To-Manim repository. Do not call offline mock runs a generated film. Missing CLI login or renderer must fail clearly. Keep generated Python/render work inside per-version directories; static checks are defense in depth, not an OS sandbox guarantee. Cancel the entire worker process tree. Preserve prior versions and bounded repair attempts. Export scene, storyboard, validation and frame evidence with editable projects; exclude CLI traces and credentials.

**Review focus:** stale approval; failed/malformed visual review; malicious or escaping result paths; cancellation/orphan subprocesses; old video falsely accepted after a failed retry.

- [x] Task 1: Add typed animation storyboard, planning instructions, schema tests and compatibility checks. Show the whole storyboard before the one confirmation.
- [x] Task 2: Vendor source with hashes/license. Add worker and adapter with tests for missing prerequisites, rejection/repair, owned results and cancellation. Reuse the native staged pipeline; replace only renderer/evidence orchestration for local compatibility.
- [x] Task 3: Wire service, animation revisions, exports and optional settings. Test real API flow with injected fixed worker results and no topic restriction.
- [x] Task 4: Render non-force scenes with the real Manim environment, inspect frames, verify packaged sources; run full regression suite and final review. State live model limitations explicitly.

## Evidence and rulings

- Initial environment: Manim 0.20.1 works in the existing repaired environment. The separate Math-To-Manim virtualenv points at an old Administrator Python and cannot start. Product worker will use the working product Python for Sol and the existing Manim Python only for rendering.
- Codex CLI exists but `codex login status` reports not logged in; no live scene-generation claim until login is supplied. The workbench Chat Completions model also remains unconfigured.
- FFmpeg/LaTeX are not on PATH. PyAV already installed supports decoding and frame extraction; LaTeX-dependent scenes must detect the prerequisite and fail accurately or use appropriate plain text when the topic permits it.

- Final review: 3 concrete findings fixed. Added validation.json to editable export (RED→GREEN); blocked dangerous identifier aliases/import members/config access (6 RED→GREEN regressions); replaced native client's parent-only timeout cleanup with product-owned process trees while preserving CLI commands/contracts. Windows Job Objects terminate descendants even after the original parent exits; both lifecycle tests complete in under 5 seconds.
- Ruling: taskkill is insufficient in the restricted Windows test environment (Access denied), and parent-only cleanup can wait for inherited pipes. Use Job Objects with kill-on-close on Windows and process groups on POSIX. No vendored file edits.
- Full suite: 69 tests passed in 6.85 seconds. Real renderer rechecked after process-lifecycle change, H.264 854×480 preview succeeded. Live CLI generation and review still blocked by missing login; no success claim.
