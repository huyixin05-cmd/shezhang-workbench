# Teach Agent

A local teaching agent used primarily through conversation in WorkBuddy or another MCP host, with an optional browser workbench. Describe a lesson, edit and approve its proposed teaching plan, then make an interactive page or teaching animation to take offline.

**Preview 0.1.0.** Bring a Chat Completions-compatible model endpoint. There is no bundled model or free inference service. Animation uses the same configured model API as lesson planning and interactive generation; it needs image input and code generation, with no Codex CLI or ChatGPT login requirement. Live model quality remains unverified.

- Teaching plans analyze the teacher's request, likely conceptual difficulties, why they are difficult, and how to explain them. Student records are not required.
- Editable step sequences specify explanation/action order, observable results, takeaways and understanding checks, with explicit revision-bound approval.
- A separate model review checks the proposed pedagogy, with at most one repair before teacher approval. Selected html-anything teaching and UI rules are loaded from pinned local originals; unrelated styles and source adapters are excluded.
- Interactive HTML with bundled KaTeX/mhchem/fonts and 213 Open Lab Components.
- Isolated browser checks, model content review, up to two repair attempts.
- Existing Manim integration, H.264 MP4 import, combined offline ZIP exports.
- Version preservation, cancellation, restart recovery; shared MCP/browser state.

Windows: install Python 3.11+, download this source and double-click `setup-workbuddy.cmd`. The local wizard installs dependencies, configures the model endpoint and writes `.data/workbuddy-mcp.json` with correct absolute paths. Add its `teach-agent` entry to WorkBuddy's MCP configuration, preserving other services, then describe a lesson in chat. API keys are entered locally and never included in the MCP JSON. Private data stays in `.data/`; never publish that directory. Double-click `start.cmd` only when you want the optional browser view.

Source setup on other platforms (not yet tested on physical macOS/Linux machines):

```sh
python -m venv .venv
# Activate it first.
python -m pip install -e '.[dev]'
python -m playwright install chromium
python -m teach_agent.onboarding --data-dir .data
# Add the generated MCP configuration to your host.
```

Generation sends the request and lesson content to your configured model service. Exported HTML/MP4/ZIP runs without that model or the workbench. Extract ZIP files completely before opening `index.html`. Editable exports contain source and reports; project re-import is not implemented yet.

Set a Python executable with Manim 0.20.1. The program reuses approved teaching decisions, calls the shared API for implementation reasoning and scene code, renders a preview, sends actual PNG frame evidence through image_url content blocks, repairs at most twice, then renders and reviews the final 720p video. No model tool-calling support or agent CLI is required. Image-request errors are explicit; there is no text-only fallback pretending to inspect frames. Usually four model calls occur after confirmation, excluding repairs. Legacy Sol plans use the same API route.

Complex formulas require LaTeX. Generated Python executes locally: static checks are defense in depth, not an OS sandbox. API credentials are passed to the worker through a private pipe and are excluded from artifact files and renderer environments. Editable exports include scene/storyboard/frame evidence and reports. Animation revisions preserve previous versions.

MCP runs `python -m teach_agent.mcp_server`, automatically starting a loopback service or reusing an existing one. No browser startup is required. Prepare the plan, wait for its summary, obtain one teacher confirmation, produce, wait, and export a local file directly in chat. The wait tool reports actual progress with a bounded wait; automatic export format selection handles HTML, MP4 and combined ZIP. Keep the MCP connection active during production: disconnecting its owned service stops unfinished jobs while preserving previous versions. Reused external services are not stopped. See the [Chinese README](README.md) for configuration and the [official WorkBuddy guide](https://www.workbuddy.ai/docs/zh/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide).

Official SDK tests exercise cold startup and the full plan/confirm/revise/export flow with deterministic model/checker fixtures, including concurrent startup and shutdown ownership. WorkBuddy's actual client conversation is not tested. The MCP host must obtain teacher approval before `confirm_and_make`; it does not automatically reuse the host's model subscription. Host-level tool permissions remain under the client's control.

Run `python -m pytest tests -q`. See [verification](VERIFICATION.md) and [third-party notices](THIRD_PARTY_NOTICES.md). Real-model generation quality/latency and another physical computer remain unverified. Component inclusion is not a claim that every component is scientifically or behaviorally validated.

MIT for original code; vendored components retain their upstream licenses. This is a loopback-only single-user tool, not a multi-user hosted service.
