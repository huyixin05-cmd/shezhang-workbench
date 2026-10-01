# Video-Only Manim Workflow

## Goal

Produce a clear MP4 explainer first. Do not make an interactive web page unless
the user explicitly asks for one.

## Planning Rules

- Start with one learning question: after watching, what can the student answer?
- Split the concept into 3 to 5 visual steps.
- Each scene should advance one idea only.
- At least half the video should show reasoning, construction, or comparison,
  not just a final result.
- Put timing targets in `plan.md`, then verify with `ffprobe`.

## Visual Rules

- Use a dark background, high-contrast arrows, and a stable palette.
- Put the core visual in the center, not in a crowded dashboard.
- Use a bottom caption for the current idea. Keep it short enough to read.
- Clear old objects before switching ideas.
- Extract 3 to 6 review frames from the final video and inspect them.

## Coding Rules

- Use `VideoScene` from `video_guard.py` when possible.
- Use `self.title_bar(...)`, `self.caption(...)`, and `self.clear_screen(...)`
  instead of ad hoc title/subtitle code.
- Run `fit_content(...)` on large groups before placing them.
- Use `self.checkpoint("name")` after dense layouts.
- Avoid rare Unicode subscript/superscript characters unless the rendered font
  is known to support them. Prefer plain `Fx`, `v_perp`, or Manim `MathTex`.

## Verification Checklist

- `python scripts/check_text.py <project>/script.py` reports no obvious text issues.
- Render logs contain no `[layout] WARN`.
- `final.mp4` exists and size is greater than zero.
- `ffprobe` duration is close to the requested duration.
- Extracted review frames show:
  - no blank frame,
  - no text outside the frame,
  - no important overlap,
  - readable Chinese text,
  - clear arrow colors and labels.

## Optional teaching-web export

When the requested destination is a teaching webpage, reuse the same scene,
render, and review process. Add `-WebOutput` and `-Title` to the render helper,
or export an existing MP4 with `scripts/export_web_clip.py`.
The exporter packages a local player, video metadata, and media without
re-rendering the clip. Include the ZIP with classroom handoff; browser-check
the player and inspect the teaching content separately.

For one scene the render helper now validates output using PyAV; multi-scene
stitching and the existing frame-extraction helper still require FFmpeg.

## When To Use Existing Plain Manim

Plain Manim is still fine for quick scratch tests, one-off geometry experiments,
or very short clips. Use this toolkit when the clip is meant to be delivered.

