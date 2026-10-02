# Teach Agent

A local teaching agent with a browser workbench and MCP adapter. Describe a lesson, edit and approve its proposed teaching plan, then make an interactive page or teaching animation to take offline.

**Preview 0.1.0.** Bring a Chat Completions-compatible model endpoint. There is no bundled model or free inference service. Animation uses the same configured model API as lesson planning and interactive generation; it needs image input and code generation, with no Codex CLI or ChatGPT login requirement. Live model quality remains unverified.

- Teaching plans analyze the teacher's request, likely conceptual difficulties, why they are difficult, and how to explain them. Student records are not required.
- Editable step sequences specify explanation/action order, observable results, takeaways and understanding checks, with explicit revision-bound approval.
- A separate model review checks the proposed pedagogy, with at most one repair before teacher approval. Selected html-anything teaching and UI rules are loaded from pinned local originals; unrelated styles and source adapters are excluded.
- Interactive HTML with bundled KaTeX/mhchem/fonts and 213 Open Lab Components.
- Isolated browser checks, model content review, up to two repair attempts.
- Existing Manim integration, H.264 MP4 import, combined offline ZIP exports.
- Version preservation, cancellation, restart recovery; shared MCP/browser state.

Windows: install Python 3.11+, download this source and double-click `start.cmd`. Configure the endpoint, model and API key in settings. The launcher stores private data in `.data/`; never publish that directory. The built-in example works without a model and is explicitly labelled as a fixed example.

Source setup on other platforms (not yet tested on physical macOS/Linux machines):

```sh
python -m venv .venv
# Activate it first.
python -m pip install -e '.[dev]'
python -m playwright install chromium
python -m teach_agent --data-dir .data --open
```

Generation sends the request and lesson content to your configured model service. Exported HTML/MP4/ZIP runs without that model or the workbench. Extract ZIP files completely before opening `index.html`. Editable exports contain source and reports; project re-import is not implemented yet.

Set a Python executable with Manim 0.20.1. The program reuses approved teaching decisions, calls the shared API for implementation reasoning and scene code, renders a preview, sends actual PNG frame evidence through image_url content blocks, repairs at most twice, then renders and reviews the final 720p video. No model tool-calling support or agent CLI is required. Image-request errors are explicit; there is no text-only fallback pretending to inspect frames. Usually four model calls occur after confirmation, excluding repairs. Legacy Sol plans use the same API route.

Complex formulas require LaTeX. Generated Python executes locally: static checks are defense in depth, not an OS sandbox. API credentials are passed to the worker through a private pipe and are excluded from artifact files and renderer environments. Editable exports include scene/storyboard/frame evidence and reports. Animation revisions preserve previous versions.

For MCP, start the workbench first and configure a stdio process running `python -m teach_agent.mcp_server`, with `PYTHONPATH` set to the source directory and `TEACH_DATA_DIR` set to the same workbench data directory. See the [Chinese README](README.md) for complete JSON configuration. The official SDK handshake is tested; WorkBuddy's actual client UI is not. The MCP host must obtain teacher approval before `confirm_and_make`; it does not automatically reuse the host's model subscription.

Run `python -m pytest tests -q`. See [verification](VERIFICATION.md) and [third-party notices](THIRD_PARTY_NOTICES.md). Real-model generation quality/latency and another physical computer remain unverified. Component inclusion is not a claim that every component is scientifically or behaviorally validated.

MIT for original code; vendored components retain their upstream licenses. This is a loopback-only single-user tool, not a multi-user hosted service.
