# Teach Agent

A local teaching agent with a browser workbench and MCP adapter. Describe a lesson, edit and approve its proposed teaching plan, then make an interactive page or teaching animation to take offline.

**Preview 0.1.0.** Bring a Chat Completions-compatible model endpoint. There is no bundled model or free inference service. Only the controlled two-force composition Manim template is implemented for animation generation today.

- Editable teaching plans with explicit revision-bound approval.
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

Set a Python executable with Manim 0.20.1 installed to render animations. Other animation topics remain explicitly unsupported. Existing H.264 MP4s can be imported or attached to an interactive version; return to the original interactive version for further edits.

For MCP, start the workbench first and configure a stdio process running `python -m teach_agent.mcp_server`, with `PYTHONPATH` set to the source directory and `TEACH_DATA_DIR` set to the same workbench data directory. See the [Chinese README](README.md) for complete JSON configuration. The official SDK handshake is tested; WorkBuddy's actual client UI is not. The MCP host must obtain teacher approval before `confirm_and_make`; it does not automatically reuse the host's model subscription.

Run `python -m pytest tests -q`. See [verification](VERIFICATION.md) and [third-party notices](THIRD_PARTY_NOTICES.md). Real-model generation quality/latency and another physical computer remain unverified. Component inclusion is not a claim that every component is scientifically or behaviorally validated.

MIT for original code; vendored components retain their upstream licenses. This is a loopback-only single-user tool, not a multi-user hosted service.
