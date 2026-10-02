# Third-party notices

Original Teach Agent code is MIT. Files under `teach_agent/vendor/` retain their original licenses and attribution; they are not claimed as original Teach Agent artwork or code.

## Open Lab Components

- Source: https://github.com/itkdm/open-lab-components
- Commit: `c336815655f233b492eb78cbfe920f078406c486`
- Copyright (c) 2026 Open Lab Components contributors; MIT.
- Original source: `teach_agent/vendor/olc/`; license: `teach_agent/vendor/olc/LICENSE`.
- Integrity manifest: `docs/provenance/olc-source.json`. Paths in the upstream snapshot manifest are relative to this vendor directory (the original acquisition directory was named `upstream`).

All 486 tracked files from the selected commit are preserved unchanged, including 213 component HTML files, 25 teaching images with metadata, runtime, site, MCP and development sources. Full Git history and installed upstream dependencies are not included. Runtime adaptation lives in Teach Agent's `materials.py`, not inside upstream files. AI-generated image labels supplied by upstream are retained; the manifest is not an independent image-rights audit.

## KaTeX and mhchem

- Source: https://github.com/KaTeX/KaTeX ; npm package `katex@0.18.10`.
- All 224 files of the published package are preserved in `teach_agent/vendor/katex/`, including 60 fonts.
- License: `teach_agent/vendor/katex/LICENSE` (MIT).
- The mhchem source contains Apache-2.0 upstream attribution for the MathJax Consortium and Martin Hensel; preserved full text: `teach_agent/vendor/katex-licenses/Apache-2.0.txt`.
- Integrity manifest: `docs/provenance/katex-source.json`; paths are relative to the corresponding vendor directory.

Exports embed the original script notices and include license notices; ZIP exports also contain `THIRD_PARTY_NOTICES.txt`.

## Prompt reference

Three original prompt files from https://github.com/clockless-org/html-anything at commit `1896831a62670eed7424b8f8e37e56c66cbf2351` (MIT-0) are preserved unchanged in `teach_agent/prompt_library/`, together with the original LICENSE. `SOURCES.json` records paths, hashes and selected sections. `prompt_sources.py` loads selected teaching, interaction and UI quality sections into actual model inputs; from `_design.md`, only spacing/radius/shadow scale bullets are selected. Local adaptation rules prioritize the confirmed teaching sequence, offline resources and consistent classroom visuals over upstream branding or layout defaults. The rest of the reference application and unrelated prompts/assets are not embedded.

## Manim workflow

The controlled force-composition scene and local video inspection were adapted from the user's existing Manim teaching workflow. Manim is an optional separately installed renderer; no Manim environment or executable is included in source exports. Python dependencies retain their respective upstream licenses as installed by pip.


## Math-To-Manim / native Sol

Source: https://github.com/HarleyCoops/Math-To-Manim at `0df6aa9d92b18d76862776a0425fda4d9f5cc023`. MIT, copyright 2025–2026 Christian H. Cooper. The unchanged `sol/*.py` snapshot and LICENSE are under `teach_agent/vendor/math_to_manim/`; integrity hashes are in `docs/provenance/math_to_manim-source.json`. The product now uses its own API orchestration outside the vendor directory. Only the standalone AST/LaTeX checker is loaded from this snapshot at runtime; the upstream CLI, agent and authentication modules remain preserved reference source and are not imported or executed.

The user's local `video-manim-toolkit` workflow guide, layout helper and text checker are preserved under `teach_agent/vendor/video_toolkit/`, with snapshot hashes in `docs/provenance/video_toolkit-source.json`. No separate upstream license was present in that local toolkit. Manim, the Python runtime and optional LaTeX are separately installed tools, not bundled executables.
