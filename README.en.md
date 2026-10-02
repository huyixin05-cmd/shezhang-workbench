# Teach Agent

A local teaching agent with two complete entry points: a browser workbench and conversation in WorkBuddy or another MCP host. Both share the same projects. Describe a lesson, edit and approve its proposed teaching plan, then make an interactive page or teaching animation to take offline.

**Preview 0.1.0.** MCP conversations default to the host's current model: it performs planning, code generation and review through normal tool calls, without another API key. The independent browser entry uses a configured Chat Completions endpoint. Animation needs image input and code generation; no Codex CLI or ChatGPT login is required. Actual WorkBuddy conversation, billing and live model quality remain unverified.

- Teaching plans analyze the teacher's request, likely conceptual difficulties, why they are difficult, and how to explain them. Student records are not required.
- Editable step sequences specify explanation/action order, observable results, takeaways and understanding checks, with explicit revision-bound approval.
- A separate model review checks the proposed pedagogy, with at most one repair before teacher approval. Selected html-anything teaching and UI rules are loaded from pinned local originals; unrelated styles and source adapters are excluded.
- Interactive HTML with bundled KaTeX/mhchem/fonts and 213 Open Lab Components.
- Isolated browser checks, model content review, up to two repair attempts.
- Existing Manim integration, H.264 MP4 import, combined offline ZIP exports.
- Version preservation, cancellation, restart recovery; shared MCP/browser state.

Windows: install Python 3.11+, download this source and double-click `setup-workbuddy.cmd`. Skip API configuration for host conversation mode; optionally configure an endpoint for independent browser use. The wizard writes `.data/workbuddy-mcp.json` with correct absolute paths. Add its `teach-agent` entry to WorkBuddy's MCP configuration, preserving other services, then describe a lesson in chat. Private data stays in `.data/`; never publish that directory. Double-click `start.cmd` for the full browser workflow.

Source setup on other platforms (not yet tested on physical macOS/Linux machines):

```sh
python -m venv .venv
# Activate it first.
python -m pip install -e '.[dev]'
python -m playwright install chromium
python -m teach_agent.onboarding --data-dir .data
# Add the generated MCP configuration to your host.
```

Generation sends requests, source and review frames to the selected model: the conversation host in host mode, or the configured endpoint in API mode. Exported HTML/MP4/ZIP runs without that model or the workbench. Extract ZIP files completely before opening `index.html`. Editable exports contain source and reports; project re-import is not implemented yet.

Set a Python executable with Manim 0.20.1. The program reuses approved teaching decisions, asks the selected model for implementation notes and scene code, renders a preview, sends real PNG frames, repairs at most twice, then renders and reviews the final 720p video. Host mode uses MCP ImageContent and requires the host to handle the tool loop; API mode uses image_url and does not require model tool calling. Usually four model steps occur after confirmation, excluding repairs. A host review is another step by the same conversation model, not an independent blind review.

Complex formulas require LaTeX. Generated Python executes locally: static checks are defense in depth, not an OS sandbox. API credentials are passed to the worker through a private pipe and are excluded from artifact files and renderer environments. Editable exports include scene/storyboard/frame evidence and reports. Animation revisions preserve previous versions.

MCP runs `python -m teach_agent.mcp_server`, automatically starting a loopback service or reusing an existing one. No browser startup is required. Prepare the plan, wait for its summary, obtain one teacher confirmation, produce, wait, and export a local file directly in chat. The wait tool reports actual progress with a bounded wait; automatic export format selection handles HTML, MP4 and combined ZIP. Keep the MCP connection active during production: disconnecting its owned service stops unfinished jobs while preserving previous versions. Reused external services are not stopped. See the [Chinese README](README.md) for configuration and the [official WorkBuddy guide](https://www.workbuddy.ai/docs/zh/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide).

In default host mode, `wait_for_lesson` can request `get_generation_step`; the host handles the returned prompts and images with its current model, calls `submit_generation_step` with JSON, and continues waiting. No credential extraction, private subscription API or MCP Sampling support is required. Model work uses the host's normal conversation billing. API mode remains explicitly selectable; there is no silent fallback. Each job snapshots its mode. Continuing a conversation-origin project in the browser visibly uses the browser's configured API. Host and API queues are separate so waiting for a conversation does not block browser work.

Official SDK tests exercise cold startup and no-extra-API host generation, plus API mode revisions and exports. Tests use deterministic model/checker fixtures. WorkBuddy's actual tool loop, image/context support and billing remain unverified. The MCP host must obtain teacher approval before `confirm_and_make`; host-level tool permissions remain under the client's control.

Run `python -m pytest tests -q`. See [verification](VERIFICATION.md) and [third-party notices](THIRD_PARTY_NOTICES.md). Real-model generation quality/latency and another physical computer remain unverified. Component inclusion is not a claim that every component is scientifically or behaviorally validated.

MIT for original code; vendored components retain their upstream licenses. This is a loopback-only single-user tool, not a multi-user hosted service.

## Experiment source collection

27 independently licensed upstream source snapshots (~104 MB) and 5 reference-only entries are available in Settings → 实验源码与参考, or via MCP `list_experiment_resources` and `export_experiment_source`. These are source resources, not 27 integrated or validated experiments. Original licenses and immutable snapshot hashes are preserved. See [the inventory](docs/experiments/README.md). Both generation entry points now use a shared interaction guide and an original offline drag/frame/fixed-timestep helper, retaining the existing apparatus style.
