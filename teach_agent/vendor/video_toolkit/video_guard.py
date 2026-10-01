from manim import *

ZH_FONT = "Microsoft YaHei"

C_BG = "#0B1020"
C_PANEL = "#111A2E"
C_TEXT = "#EAF2FF"
C_MUTED = "#8EA0C6"
C_MAIN = "#4CC9F0"
C_ACCENT = "#FFD166"
C_RESULT = "#FF6B6B"
C_OK = "#3DDC97"
C_GRID = "#24304A"

SAFE_X = 6.85
SAFE_Y = 3.82
CONTENT_MAX_W = 12.8
CONTENT_MAX_H = 5.45


def text_label(text, size=28, color=C_TEXT, font=ZH_FONT, **kwargs):
    return Text(text, font=font, font_size=size, color=color, **kwargs)


def fit_content(mobj, max_w=CONTENT_MAX_W, max_h=CONTENT_MAX_H):
    if mobj.width > max_w:
        mobj.scale_to_fit_width(max_w)
    if mobj.height > max_h:
        mobj.scale_to_fit_height(max_h)
    return mobj


def vector_arrow(start, end, color=C_MAIN, stroke_width=7, buff=0):
    return Arrow(
        start=start,
        end=end,
        buff=buff,
        color=color,
        stroke_width=stroke_width,
        max_tip_length_to_length_ratio=0.18,
    )


def soft_grid(opacity=0.34):
    grid = NumberPlane(
        x_range=[-8, 8, 1],
        y_range=[-5, 5, 1],
        background_line_style={
            "stroke_color": C_GRID,
            "stroke_width": 1,
            "stroke_opacity": opacity,
        },
        axis_config={"stroke_opacity": 0},
    )
    grid._video_guard_ignore = True
    return grid


def info_card(lines, corner=UR, width=4.0, font_size=22):
    panel = RoundedRectangle(
        width=width,
        height=0.56 * len(lines) + 0.38,
        corner_radius=0.08,
        fill_color=C_PANEL,
        fill_opacity=0.84,
        stroke_color=C_MUTED,
        stroke_width=1.4,
    )
    body = VGroup(*[
        text_label(line, font_size) for line in lines
    ]).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
    fit_content(body, max_w=width - 0.4, max_h=panel.height - 0.25)
    body.move_to(panel)
    return VGroup(panel, body).to_corner(corner, buff=0.42)


def _ignore(mobj):
    return bool(getattr(mobj, "_video_guard_ignore", False))


def _has_points(mobj):
    try:
        return len(mobj.family_members_with_points()) > 0
    except Exception:
        return False


def _bbox(mobj):
    return (
        mobj.get_left()[0],
        mobj.get_right()[0],
        mobj.get_bottom()[1],
        mobj.get_top()[1],
    )


def _area(mobj):
    left, right, bottom, top = _bbox(mobj)
    return max(0, right - left) * max(0, top - bottom)


def _overlap_area(a, b):
    al, ar, ab, at = _bbox(a)
    bl, br, bb, bt = _bbox(b)
    return max(0, min(ar, br) - max(al, bl)) * max(0, min(at, bt) - max(ab, bb))


def _desc(mobj):
    value = getattr(mobj, "text", None)
    if value:
        return f"Text({value[:18]!r})"
    return type(mobj).__name__


class VideoScene(Scene):
    """Scene base class with video-focused layout and style helpers."""

    def setup(self):
        self.camera.background_color = C_BG
        self._title = None
        self._caption = None
        self._layout_warns = 0

    def add_backdrop(self):
        blobs = VGroup(
            Circle(radius=5).set_fill(C_MAIN, 0.045).set_stroke(width=0).move_to([-5, 3, 0]),
            Circle(radius=5).set_fill("#B794F6", 0.04).set_stroke(width=0).move_to([5.4, -3, 0]),
        )
        for blob in blobs:
            blob._video_guard_ignore = True
        blobs._video_guard_ignore = True
        self.add(blobs)
        return blobs

    def title_bar(self, text, size=34):
        title = text_label(text, size, C_TEXT).to_edge(UP, buff=0.28)
        fit_content(title, max_w=CONTENT_MAX_W, max_h=0.75)
        underline = Line(title.get_left(), title.get_right(), color=C_MUTED, stroke_width=2)
        underline.next_to(title, DOWN, buff=0.08)
        group = VGroup(title, underline)
        if self._title is None:
            self.play(FadeIn(group, shift=DOWN * 0.18), run_time=0.55)
            self._title = group
        else:
            self.play(ReplacementTransform(self._title, group), run_time=0.45)
            self._title = group
        return group

    def caption(self, text, wait=1.4, size=24, color=C_TEXT, accent=C_ACCENT):
        txt = text_label(text, size, color)
        fit_content(txt, max_w=CONTENT_MAX_W - 0.8, max_h=0.55)
        panel = RoundedRectangle(
            width=txt.width + 0.75,
            height=txt.height + 0.34,
            corner_radius=0.12,
            stroke_width=0,
            fill_color="#0E1828",
            fill_opacity=0.76,
        )
        mark = RoundedRectangle(
            width=0.08,
            height=txt.height + 0.16,
            corner_radius=0.04,
            stroke_width=0,
            fill_color=accent,
            fill_opacity=1,
        )
        txt.move_to(panel)
        mark.move_to(panel.get_left()).shift(RIGHT * 0.17)
        group = VGroup(panel, mark, txt).to_edge(DOWN, buff=0.56)
        group._video_guard_ignore = False
        if self._caption is None:
            self.play(FadeIn(group, shift=UP * 0.18), run_time=0.35)
        else:
            self.play(FadeOut(self._caption, shift=UP * 0.12), FadeIn(group, shift=UP * 0.18), run_time=0.35)
        self._caption = group
        self.wait(wait)
        return group

    def clear_screen(self, *keep):
        keep_set = set(keep)
        if self._title is not None:
            keep_set.add(self._title)
        targets = [m for m in self.mobjects if m not in keep_set and not _ignore(m)]
        if targets:
            self.play(*[FadeOut(m) for m in targets], run_time=0.45)
        if self._caption not in keep_set:
            self._caption = None

    def checkpoint(self, label="checkpoint"):
        self.layout_check(label)

    def wait(self, *args, **kwargs):
        super().wait(*args, **kwargs)
        self.layout_check("wait")

    def layout_check(self, label="layout"):
        problems = []
        top_level = [m for m in self.mobjects if not _ignore(m) and _has_points(m) and _area(m) > 1e-4]
        for mobj in top_level:
            left, right, bottom, top = _bbox(mobj)
            if left < -SAFE_X or right > SAFE_X or bottom < -SAFE_Y or top > SAFE_Y:
                problems.append(
                    f"out_of_bounds {_desc(mobj)} x[{left:.2f},{right:.2f}] y[{bottom:.2f},{top:.2f}]"
                )

        texts = []
        for mobj in self.mobjects:
            if _ignore(mobj):
                continue
            for sub in mobj.get_family():
                if isinstance(sub, (Text, MarkupText)) and _has_points(sub) and _area(sub) > 0.35:
                    texts.append(sub)

        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                small = min(_area(texts[i]), _area(texts[j]))
                if small > 0 and _overlap_area(texts[i], texts[j]) > 0.65 * small:
                    problems.append(f"text_overlap {_desc(texts[i])} with {_desc(texts[j])}")

        for problem in problems:
            self._layout_warns += 1
            print(f"[layout][{label}] WARN {problem}")

    def tear_down(self):
        print(f"[layout] DONE warnings={self._layout_warns}")
        super().tear_down()
