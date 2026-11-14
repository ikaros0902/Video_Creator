"""Manim scenes for engineering explainer animations (3Blue1Brown-style).

Rendered by vc/manim_render.py. Each scene reads cue times from VC_MANIM_CUES and
writes the actual trigger times to VC_MANIM_SYNC, so the animation follows the
narration word timing.

Visual rules (one color = one meaning, kept for the whole video):
  white  = text and outlines     steel = solid sheet metal
  cyan   = mid-plane / tool      amber = thickness and measurement
  coral  = gaps and errors
"""
from __future__ import annotations

import json
import os

import numpy as np
from manim import (BOLD, DEGREES, DOWN, LEFT, ORIGIN, PI, RIGHT, UL, UP, Arc, Circle, Create, Cross,
                   DashedLine, DoubleArrow, FadeIn, FadeOut, GrowFromCenter, GrowFromEdge, ImageMobject,
                   LaggedStart, Line, MovingCameraScene, Polygon, Prism, Rectangle, RoundedRectangle, Square,
                   Text, ThreeDScene, Transform, VGroup, VMobject, config, Dot)

NAVY = "#06213D"
CYAN = "#1EB8EC"
AMBER = "#F5B841"
CORAL = "#FF6B5A"
STEEL = "#7FA7D9"
MUTED = "#9FB3CC"
WHITE = "#FFFFFF"
FONT = "Segoe UI"

config.background_color = NAVY


def txt(s: str, size: float = 36, color: str = WHITE, bold: bool = False) -> Text:
    return Text(s, font=FONT, font_size=size, color=color, weight=BOLD if bold else "NORMAL")


def path(points, color=WHITE, width=5.0) -> VMobject:
    return VMobject().set_points_as_corners([np.array([x, y, 0.0]) for x, y in points]).set_stroke(color, width)


def grid() -> VGroup:
    g = VGroup(*[Line([x, -6, 0], [x, 6, 0]) for x in np.arange(-10.4, 10.41, 0.8)],
               *[Line([-10.4, y, 0], [10.4, y, 0]) for y in np.arange(-6.4, 6.41, 0.8)])
    return g.set_stroke(WHITE, 1, opacity=0.05)


class SyncMixin:
    """`at(cue, ...)` waits until the narration reaches the cue word, then plays."""

    DEFAULT_CUES: dict[str, float] = {}
    DEFAULT_DURATION = 10.0
    DEFAULT_NARRATION_END = 9.0

    def load_cues(self):
        p = os.environ.get("VC_MANIM_CUES")
        if p:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            self.cues, self.total, self.opts = d["cues"], d["duration"], d.get("options", {})
            self.narration_end = d.get("narration_end", self.total)
        else:
            self.cues, self.total, self.opts = dict(self.DEFAULT_CUES), self.DEFAULT_DURATION, {}
            self.narration_end = self.DEFAULT_NARRATION_END
        self.events: list[dict] = []

    @property
    def now(self) -> float:
        return self.renderer.time

    def wait_until(self, t: float) -> None:
        gap = t - self.now
        if gap > 1e-3:
            self.wait(gap)

    def at(self, cue: str, *anims, run_time: float = 0.6, lead: float = 0.15) -> None:
        # Start slightly before the word so the motion lands on it
        target = self.cues[cue]
        self.wait_until(target - lead)
        self.events.append({"cue": cue, "target": round(target, 3), "actual": round(self.now + lead, 3)})
        if anims:
            self.play(*anims, run_time=run_time)

    def finish(self) -> None:
        self.wait_until(self.total)
        p = os.environ.get("VC_MANIM_SYNC")
        if p:
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"events": self.events, "end": round(self.now, 3)}, f, indent=2)


class SyncedScene(SyncMixin, MovingCameraScene):
    def setup(self):
        super().setup()
        self.load_cues()
        self.add(grid())


class Synced3DScene(SyncMixin, ThreeDScene):
    def setup(self):
        super().setup()
        self.load_cues()

    def fixed(self, *mobs):
        """Labels that stay flat on screen while the 3D camera orbits."""
        self.add_fixed_in_frame_mobjects(*mobs)
        self.remove(*mobs)
        return mobs[0] if len(mobs) == 1 else VGroup(*mobs)


# ---------------------------------------------------------------------------
# s02: why engineers replace a thin solid with a mid-plane shell (3D orbit)
# ---------------------------------------------------------------------------

class ThinShellScene(Synced3DScene):
    DEFAULT_CUES = {"thin": 3.1, "blocks": 7.7, "slow": 10.2, "replace": 12.5, "middle": 14.9,
                    "name": 16.13, "number": 18.47}
    DEFAULT_DURATION = 20.0

    def construct(self):
        L, W, T = 5.2, 3.0, 0.4
        # Shift camera center down so the plate sits higher, leaving room for captions
        self.set_camera_orientation(phi=62 * DEGREES, theta=-58 * DEGREES, zoom=1.0,
                                    frame_center=[0, 0, -0.9])
        self.begin_ambient_camera_rotation(rate=0.022)

        head = self.fixed(txt(self.opts.get("head_text", "Why a thin shell?"), 44, WHITE, bold=True).to_corner(UL, buff=0.55))
        plate = Prism(dimensions=[L, W, T]).set_fill(STEEL, 0.55).set_stroke(WHITE, 1.5, 0.8)
        self.play(FadeIn(head, shift=0.2 * DOWN), FadeIn(plate), run_time=1.2)

        # 厚度用工程圖的尺寸線表示：從右前轉角的上下邊往外拉延伸線，箭頭畫在延伸線之間。
        # 箭頭在板子外面，不會被板子的邊線蓋住，也看得出量的是哪一段。
        cx0, cy0, ext = L / 2, -W / 2, 0.75
        ax, ay = cx0 + ext - 0.12, cy0

        def ext_line(z):
            return Line([cx0 + 0.04, cy0, z], [cx0 + ext, cy0, z]).set_stroke(AMBER, 2.5)

        thin = VGroup(ext_line(T / 2), ext_line(-T / 2),
                      DoubleArrow([ax, ay, -T / 2], [ax, ay, T / 2], buff=0, stroke_width=5,
                                  tip_length=0.07, max_tip_length_to_length_ratio=0.45, color=AMBER))
        thin_lab = self.fixed(txt("Very thin", 40, AMBER, bold=True).move_to([4.6, -0.3, 0]))
        self.at("thin", Create(thin), FadeIn(thin_lab), run_time=0.7)

        # Solid mesh: blocks on the top face and through the thickness
        mesh = VGroup()
        zt = T / 2 + 0.005
        for x in np.linspace(-L / 2, L / 2, 25)[1:-1]:
            mesh.add(Line([x, -W / 2, zt], [x, W / 2, zt]))
            mesh.add(Line([x, -W / 2 - 0.005, -T / 2], [x, -W / 2 - 0.005, T / 2]))
        for y in np.linspace(-W / 2, W / 2, 15)[1:-1]:
            mesh.add(Line([-L / 2, y, zt], [L / 2, y, zt]))
        for z in np.linspace(-T / 2, T / 2, 4)[1:-1]:
            mesh.add(Line([-L / 2, -W / 2 - 0.005, z], [L / 2, -W / 2 - 0.005, z]))
            # 右端面（+x）也看得到，一樣要畫網格
            mesh.add(Line([L / 2 + 0.005, -W / 2, z], [L / 2 + 0.005, W / 2, z]))
        for y in np.linspace(-W / 2, W / 2, 15)[1:-1]:
            mesh.add(Line([L / 2 + 0.005, y, -T / 2], [L / 2 + 0.005, y, T / 2]))
        mesh.set_stroke(CORAL, 1.6, 0.9)
        mesh_lab = self.fixed(txt("Solid: many tiny blocks", 40, CORAL, bold=True).move_to([0, -2.0, 0]))
        # 所有面的網格同時畫出，不會有某一面晚出現
        self.at("blocks", FadeOut(thin_lab), FadeOut(thin), Create(mesh, lag_ratio=0), FadeIn(mesh_lab),
                run_time=0.9)

        # Model size and solve time, shown without numbers
        def meter(label: str, y: float):
            lab = txt(label, 32, MUTED).move_to([4.2, y + 0.45, 0])
            track = Rectangle(width=2.6, height=0.22).move_to([4.2, y, 0]).set_stroke(MUTED, 1.5).set_fill(opacity=0)
            bar = Rectangle(width=2.6, height=0.22).move_to([4.2, y, 0]).set_stroke(width=0).set_fill(CORAL, 1)
            return lab, track, bar
        m1, m2 = meter("Model size", 2.4), meter("Solve time", 1.35)
        meters = self.fixed(*m1, *m2)
        bars = VGroup(m1[2], m2[2])
        self.at("slow", FadeIn(VGroup(m1[0], m1[1], m2[0], m2[1])),
                *[GrowFromEdge(b, LEFT) for b in bars], run_time=0.9)

        self.at("replace", FadeOut(mesh), FadeOut(mesh_lab), plate.animate.set_fill(STEEL, 0.12).set_stroke(opacity=0.3),
                run_time=0.9)
        mid = Rectangle(width=L, height=W).set_stroke(CYAN, 3).set_fill(CYAN, 0.55)
        # 上下各半個板厚：同一組尺寸線，中間多一條延伸線對齊中面
        half = VGroup(
            ext_line(T / 2), ext_line(-T / 2), ext_line(0).set_stroke(CYAN, 3),
            DoubleArrow([ax, ay, 0], [ax, ay, T / 2], buff=0, stroke_width=4, tip_length=0.05,
                        max_tip_length_to_length_ratio=0.45, color=AMBER),
            DoubleArrow([ax, ay, -T / 2], [ax, ay, 0], buff=0, stroke_width=4, tip_length=0.05,
                        max_tip_length_to_length_ratio=0.45, color=AMBER))
        self.at("middle", FadeIn(mid), Create(half), run_time=0.9)
        name = self.fixed(txt(self.opts.get("name_text", "Mid-plane shell"), 52, CYAN, bold=True).move_to([0, -2.0, 0]))
        self.at("name", FadeIn(name, shift=0.15 * UP), run_time=0.6)

        card_txt = txt("Thickness = t", 40, AMBER, bold=True)
        card = self.fixed(VGroup(RoundedRectangle(corner_radius=0.15, width=card_txt.width + 0.7, height=0.95)
                                 .set_stroke(AMBER, 3).set_fill(NAVY, 0.9), card_txt).move_to([-4.6, -0.6, 0]))
        self.at("number", FadeIn(card, shift=0.15 * UP),
                bars[0].animate.stretch_to_fit_width(0.5, about_edge=LEFT).set_fill(CYAN),
                bars[1].animate.stretch_to_fit_width(0.5, about_edge=LEFT).set_fill(CYAN), run_time=0.8)
        self.finish()


# ---------------------------------------------------------------------------
# s07: whole assembly, manual time vs automated time, then the outro
# ---------------------------------------------------------------------------

MANUAL_MAX_S = 12 * 3600
ACT_S = 50.1           # Batch runtime reference value (facts.yaml batch_runtime)


class RoiTimeScene(SyncedScene):
    DEFAULT_CUES = {"grid": 0.2, "each": 3.97, "act": 7.4, "result": 10.07}
    DEFAULT_DURATION = 13.6
    DEFAULT_NARRATION_END = 10.4

    def construct(self):
        head = txt("Whole chassis: 35 parts", 44, WHITE, bold=True).to_corner(UL, buff=0.55)
        cells = VGroup(*[Square(0.62).set_stroke(CORAL, 2).set_fill(CORAL, 0.35) for _ in range(35)])
        cells.arrange_in_grid(rows=5, cols=7, buff=0.14).move_to([-3.4, 0.55, 0])
        hand = txt("By hand", 40, CORAL, bold=True).move_to([3.3, 1.9, 0])
        hours = txt("6–12 h", 96, CORAL, bold=True).next_to(hand, DOWN, buff=0.25)
        # 旁白第 0.2 秒就念到 "hand"，標題和方格一起出現，不另外佔用開頭時間
        self.at("grid", FadeIn(head, shift=0.2 * DOWN), LaggedStart(*[FadeIn(c, scale=0.7) for c in cells], lag_ratio=0.03),
                FadeIn(hand), FadeIn(hours, shift=0.15 * UP), run_time=1.6, lead=0.2)

        one = cells[0]
        each = txt("10–20 min each, plus checks", 34, MUTED).next_to(cells, DOWN, buff=0.35)
        self.at("each", one.animate.set_fill(CORAL, 0.9).scale(1.15), FadeIn(each), run_time=0.6)

        # Same time scale: 12 h = full bar. 50.1 s is drawn at its true length (minimum 2 px).
        x0, full = -6.0, 11.0
        y_man, y_act = 0.9, -0.6
        man6 = Rectangle(width=full / 2, height=0.5).set_stroke(width=0).set_fill(CORAL, 0.95)
        man6.move_to([x0 + full / 4, y_man, 0])
        man12 = Rectangle(width=full / 2, height=0.5).set_stroke(width=0).set_fill(CORAL, 0.4)
        man12.move_to([x0 + 3 * full / 4, y_man, 0])
        man_lab = txt("By hand  6–12 h", 36, CORAL, bold=True).next_to(man6, UP, buff=0.2).align_to(man6, LEFT)
        w_act = max(full * ACT_S / MANUAL_MAX_S, 0.016)
        act_bar = Rectangle(width=w_act, height=0.5).set_stroke(width=0).set_fill(CYAN, 1)
        act_bar.move_to([x0 + w_act / 2, y_act, 0])
        act_lab = txt("ACT  50.1 s", 44, CYAN, bold=True).next_to(act_bar, RIGHT, buff=0.35)
        scale_lab = txt("Same time scale", 30, MUTED).move_to([3.5, -1.85, 0])
        self.at("act", FadeOut(VGroup(head, hand, hours, each)),
                Transform(cells, VGroup(man6, man12)), FadeIn(man_lab), run_time=1.0)
        self.at("result", FadeIn(act_bar), FadeIn(act_lab, shift=0.15 * RIGHT), FadeIn(scale_lab), run_time=0.6)

        # Outro after the last word
        self.wait_until(self.narration_end + 0.4)
        title = txt(self.opts.get("outro_title", "CAD Batch Validator v3.0"), 64, WHITE, bold=True)
        brand = self.opts.get("brand_dir")
        if self.opts.get("logo") and brand:
            primary = ImageMobject(os.path.join(brand, "primary_white.png")).set_height(0.62)
            secondary = ImageMobject(os.path.join(brand, "secondary_white.png")).set_height(0.8)
            sep = Line([0, -0.35, 0], [0, 0.35, 0]).set_stroke(WHITE, 2, 0.4)
            row = [primary, sep, secondary]
            primary.move_to([-1.9, -1.1, 0]); sep.move_to([0, -1.1, 0]); secondary.move_to([1.9, -1.1, 0])
            title.move_to([0, 0.5, 0])
            self.play(FadeOut(VGroup(cells, man_lab, act_bar, act_lab, scale_lab), shift=0.3 * UP),
                      FadeIn(title, shift=0.2 * UP), *[FadeIn(m) for m in row], run_time=0.9)
        else:
            title.move_to([0, 0.2, 0])
            self.play(FadeOut(VGroup(cells, man_lab, act_bar, act_lab, scale_lab), shift=0.3 * UP),
                      FadeIn(title, shift=0.2 * UP), run_time=0.9)
        self.finish()


# ---------------------------------------------------------------------------
# e05 (executive cut): test model, manual estimate vs automated run, same time
# scale. Kept separate from RoiTimeScene so the full version (s07) never changes.
# ---------------------------------------------------------------------------

class ExecTimeScene(SyncedScene):
    DEFAULT_CUES = {"model": 0.5, "estimates": 1.6, "repairs": 5.0, "act": 7.4, "minute": 10.0}
    DEFAULT_DURATION = 14.0
    DEFAULT_NARRATION_END = 10.6

    def construct(self):
        cards = self.opts.get("cards", {})
        manual_max_h = self.opts.get("manual_max_h", MANUAL_MAX_S / 3600)
        act_s = self.opts.get("act_s", ACT_S)
        manual_max_s = manual_max_h * 3600

        head = txt(cards.get("head", ""), 44, WHITE, bold=True).to_corner(UL, buff=0.55)
        self.at("model", FadeIn(head), lead=0.2)

        # Same time scale as RoiTimeScene: full bar = manual_max_h hours.
        x0, full = -6.0, 11.0
        y_man, y_act = 0.9, -1.0
        man_half1 = Rectangle(width=full / 2, height=0.5).set_stroke(width=0).set_fill(CORAL, 0.95)
        man_half1.move_to([x0 + full / 4, y_man, 0])
        man_half2 = Rectangle(width=full / 2, height=0.5).set_stroke(width=0).set_fill(CORAL, 0.4)
        man_half2.move_to([x0 + 3 * full / 4, y_man, 0])
        manual_bar = VGroup(man_half1, man_half2)
        manual_lab = txt(cards.get("manual", ""), 40, CORAL, bold=True).next_to(manual_bar, UP, buff=0.2).align_to(manual_bar, LEFT)
        self.at("estimates", GrowFromEdge(manual_bar, LEFT), FadeIn(manual_lab), run_time=1.0)

        manual_note = txt(cards.get("manual_note", ""), 30, MUTED).next_to(manual_bar, DOWN, buff=0.3).align_to(manual_bar, LEFT)
        self.at("repairs", FadeIn(manual_note))

        w_act = max(full * act_s / manual_max_s, 0.016)
        act_bar = Rectangle(width=w_act, height=0.5).set_stroke(width=0).set_fill(CYAN, 1)
        act_bar.move_to([x0 + w_act / 2, y_act, 0])
        act_lab = txt(cards.get("act", ""), 44, CYAN, bold=True).next_to(act_bar, RIGHT, buff=0.35)
        act_note = txt(cards.get("act_note", ""), 30, MUTED).next_to(act_lab, DOWN, buff=0.15).align_to(act_lab, LEFT)
        scale_lab = txt(cards.get("scale", ""), 30, MUTED).move_to([3.5, -1.85, 0])
        self.at("act", FadeIn(act_bar), FadeIn(act_lab, shift=0.15 * RIGHT), FadeIn(act_note), FadeIn(scale_lab))

        underline = Line([act_lab.get_left()[0], act_lab.get_bottom()[1] - 0.08, 0],
                         [act_lab.get_right()[0], act_lab.get_bottom()[1] - 0.08, 0]).set_stroke(AMBER, 3)
        self.at("minute", Create(underline), run_time=0.5)

        # Outro after the last word (same layout as RoiTimeScene)
        self.wait_until(self.narration_end + 0.4)
        title = txt(self.opts.get("outro_title", "CAD Batch Validator v3.0"), 64, WHITE, bold=True)
        on_screen = VGroup(head, manual_bar, manual_lab, manual_note, act_bar, act_lab, act_note, scale_lab, underline)
        brand = self.opts.get("brand_dir")
        if self.opts.get("logo") and brand:
            primary = ImageMobject(os.path.join(brand, "primary_white.png")).set_height(0.62)
            secondary = ImageMobject(os.path.join(brand, "secondary_white.png")).set_height(0.8)
            sep = Line([0, -0.35, 0], [0, 0.35, 0]).set_stroke(WHITE, 2, 0.4)
            row = [primary, sep, secondary]
            primary.move_to([-1.9, -1.1, 0]); sep.move_to([0, -1.1, 0]); secondary.move_to([1.9, -1.1, 0])
            title.move_to([0, 0.5, 0])
            self.play(FadeOut(on_screen, shift=0.3 * UP), FadeIn(title, shift=0.2 * UP),
                      *[FadeIn(m) for m in row], run_time=0.9)
        else:
            title.move_to([0, 0.2, 0])
            self.play(FadeOut(on_screen, shift=0.3 * UP), FadeIn(title, shift=0.2 * UP), run_time=0.9)
        self.finish()


# ---------------------------------------------------------------------------
# s04: why the built-in tool fails, and the 4 steps of the automated method
# ---------------------------------------------------------------------------

def offset_polyline(points, dist):
    """Offset a polyline to its right side (downward for left-to-right) by `dist`,
    with mitered corners. Sheet metal keeps the same thickness through bends,
    so the bottom surface is the top surface offset by the thickness."""
    pts = [np.array(p, dtype=float) for p in points]
    dirs = [(b - a) / np.linalg.norm(b - a) for a, b in zip(pts, pts[1:])]
    norms = [np.array([d[1], -d[0]]) for d in dirs]
    out = [tuple(pts[0] + norms[0] * dist)]
    for i in range(1, len(pts) - 1):
        n = norms[i - 1] + norms[i]
        n = n / np.linalg.norm(n)
        out.append(tuple(pts[i] + n * dist / float(np.dot(n, norms[i]))))
    out.append(tuple(pts[-1] + norms[-1] * dist))
    return [(round(x, 4), round(y, 4)) for x, y in out]


# Cross-section of a plate with a stamped step. Thickness = 0.6 units, constant through the step.
THICK = 0.6
TOP = [(-6.6, 0.9), (-0.5, 0.9), (0.0, 0.5), (6.6, 0.5)]
BOT = offset_polyline(TOP, THICK)
MID = offset_polyline(TOP, THICK / 2)


def y_on(points, x):
    xs, ys = zip(*points)
    return float(np.interp(x, xs, ys))


class OffsetMechanismScene(SyncedScene):
    DEFAULT_CUES = {"pair": 2.33, "step": 5.67, "vote": 11.87, "largest": 16.4, "offset": 18.1,
                    "inward": 20.1, "nopairs": 24.03, "shapes": 25.1, "hem": 27.5, "dent": 29.97,
                    "probe": 32.67, "review": 38.47}
    DEFAULT_DURATION = 39.6

    def heading(self, s: str, color: str) -> Text:
        return txt(s, 44, color, bold=True).to_corner(UL, buff=0.55)

    def construct(self):
        frame = self.camera.frame

        # --- Beat A: face pairing breaks at the stamped step -----------------
        head = self.heading("Why the built-in tool fails", WHITE)
        top, bot = path(TOP), path(BOT)
        fill = Polygon(*[np.array([x, y, 0]) for x, y in TOP + BOT[::-1]],
                       stroke_width=0, fill_color=STEEL, fill_opacity=0.22)
        self.play(FadeIn(head, shift=0.2 * DOWN), FadeIn(fill), Create(top), Create(bot), run_time=1.4)

        xs = [-5.8, -4.6, -3.4, -2.2, -1.1, 1.3, 2.5, 3.7, 4.9, 6.0]
        pairs = VGroup(*[DoubleArrow([x, y_on(BOT, x) + 0.03, 0], [x, y_on(TOP, x) - 0.03, 0], buff=0,
                                     stroke_width=3, tip_length=0.12, color=MUTED) for x in xs])
        pair_lab = txt("Each top face  ↔  one bottom face", 36, MUTED).move_to([0, 2.0, 0])
        self.at("pair", LaggedStart(*[GrowFromCenter(p) for p in pairs], lag_ratio=0.08),
                FadeIn(pair_lab, shift=0.15 * UP), run_time=1.3)

        # Face by face, the old tool pairs each top face with one bottom face. At the bends the
        # face edges do not line up, so each piece of midsurface stops short of the corner.
        z = 0.5  # zoom factor for the close-up on the step
        corners = [np.array([MID[1][0], MID[1][1], 0]), np.array([MID[2][0], MID[2][1], 0])]
        trim = 0.2
        def trimmed(a, b, cut_a, cut_b):
            a, b = np.array([*a, 0.0]), np.array([*b, 0.0])
            d = (b - a) / np.linalg.norm(b - a)
            return DashedLine(a + d * cut_a, b - d * cut_b, dash_length=0.1).set_stroke(CYAN, 6)
        mids = VGroup(trimmed(MID[0], MID[1], 0, trim), trimmed(MID[1], MID[2], trim, trim),
                      trimmed(MID[2], MID[3], trim, 0))
        rings = VGroup(*[Circle(radius=0.24, color=CORAL, stroke_width=5).move_to(c) for c in corners])
        gap_lab = txt("No partner  →  gap", 44, CORAL, bold=True).scale(z).move_to([-0.2, 1.45, 0])
        self.at("step", FadeOut(head), FadeOut(pair_lab), frame.animate.scale(z).move_to([-0.2, 0.55, 0]),
                run_time=1.0)
        self.play(Create(mids), run_time=0.8)
        self.play(Create(rings), FadeIn(gap_lab, shift=0.1 * UP), run_time=1.0)

        # --- Beat B: measure thickness, keep the value on the largest area ---
        head = self.heading("1  Measure the thickness", AMBER)
        self.at("vote", frame.animate.scale(1 / z).move_to(ORIGIN),
                FadeOut(VGroup(pairs, mids, rings, gap_lab)), FadeIn(head), run_time=1.0)
        probes = VGroup(*[DoubleArrow([x, y_on(BOT, x) + 0.03, 0], [x, y_on(TOP, x) - 0.03, 0], buff=0,
                                      stroke_width=4, tip_length=0.13, color=AMBER)
                          for x in (-5.4, -3.8, -2.2, 1.8, 3.4, 5.0)])
        base = Line([2.2, 1.5, 0], [6.4, 1.5, 0]).set_stroke(MUTED, 2)
        values, heights = ("0.8", "1.2", "2.5 mm"), (0.35, 1.05, 0.25)
        bars = VGroup(*[Rectangle(width=0.8, height=h, stroke_width=0, fill_color=MUTED, fill_opacity=0.8)
                        .move_to([2.9 + 1.4 * i, 1.5 + h / 2, 0]) for i, h in enumerate(heights)])
        vlabs = VGroup(*[txt(v, 30, MUTED).next_to(b, DOWN, buff=0.12) for v, b in zip(values, bars)])
        # 標題放在最高長條與「t = 1.2 mm」標籤的上方，不重疊
        chart_lab = txt("Area at each measured gap", 30, MUTED).move_to([4.3, 3.55, 0])
        self.play(LaggedStart(*[GrowFromCenter(p) for p in probes], lag_ratio=0.12), run_time=1.0)
        self.play(Create(base), FadeIn(chart_lab), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.2),
                  FadeIn(vlabs), run_time=1.2)
        t_lab = txt("t = 1.2 mm", 44, AMBER, bold=True).next_to(bars[1], UP, buff=0.2)
        self.at("largest", bars[1].animate.set_fill(AMBER, 1.0), vlabs[1].animate.set_color(AMBER),
                FadeIn(t_lab, shift=0.15 * UP), run_time=0.6)

        # --- Beat C: copy one outer surface and move it in by half -----------
        new_head = self.heading("2  Copy one surface, move it in by ½ t", CYAN)
        skin = top.copy().set_stroke(CYAN, 8)
        self.at("offset", Transform(head, new_head), FadeOut(VGroup(probes, base, bars, vlabs, chart_lab, t_lab)),
                bot.animate.set_stroke(opacity=0.3), fill.animate.set_fill(opacity=0.12), Create(skin), run_time=0.9)
        half = VGroup(*[DoubleArrow([x, y_on(TOP, x), 0], [x, y_on(TOP, x) - 0.3, 0], buff=0, stroke_width=3,
                                    tip_length=0.1, color=AMBER) for x in (-2.6, 2.6)])
        # 標籤放在上表面之上，避免壓到往下移的青色線
        half_lab = txt("½ t", 30, AMBER, bold=True).next_to(half[0], UP, buff=0.12)
        # Move along the surface normal by half the thickness: the copy stays parallel through the step
        self.at("inward", Transform(skin, path(MID, CYAN, 8)), FadeIn(half), FadeIn(half_lab), run_time=1.0)
        # Follow the new surface across the step to show it stays connected
        self.play(frame.animate.scale(0.6).move_to([0.0, 0.45, 0]), FadeOut(head), run_time=1.0)
        ok_lab = txt("One surface  →  no pairs to break", 44, CYAN, bold=True).scale(0.6).move_to([0.0, 1.55, 0])
        self.at("nopairs", FadeIn(ok_lab, shift=0.1 * UP), run_time=0.6)

        # --- Beat D: repair special shapes (closed hem, round dent) ----------
        section = VGroup(top, bot, fill, skin, half, half_lab, ok_lab)
        head = self.heading("3  Repair special shapes", AMBER)
        self.at("shapes", frame.animate.scale(1 / 0.6).move_to(ORIGIN), FadeOut(section), FadeIn(head),
                run_time=1.0)

        # Left: 180-degree closed hem in cross-section (outer bend R = t, inner radius 0)
        cx = -2.4
        hem = VGroup(
            Line([-6.4, 1.2, 0], [cx, 1.2, 0]), Arc(radius=0.6, start_angle=PI / 2, angle=-PI, arc_center=[cx, 0.6, 0]),
            Line([cx, 0.0, 0], [-4.6, 0.0, 0]), Line([-4.6, 0.0, 0], [-4.6, 0.6, 0]),
            # Contact line between the two layers runs all the way to the fold (inner radius 0)
            Line([cx, 0.6, 0], [-6.4, 0.6, 0]),
        ).set_stroke(WHITE, 4)
        hem_fill = VGroup(Rectangle(width=4.0, height=0.6).move_to([-4.4, 0.9, 0]),
                          Rectangle(width=2.2, height=0.6).move_to([-3.5, 0.3, 0])).set_stroke(width=0).set_fill(STEEL, 0.22)
        hem_mids = VGroup(Line([-6.4, 0.9, 0], [cx, 0.9, 0]), Line([-4.6, 0.3, 0], [cx, 0.3, 0])).set_stroke(CYAN, 6)
        bridge = Arc(radius=0.3, start_angle=PI / 2, angle=-PI, arc_center=[cx, 0.6, 0]).set_stroke(AMBER, 8)
        hem_lab = txt("Closed hem", 34, MUTED).move_to([-4.2, 2.0, 0])
        bridge_lab = txt("Bridge", 40, AMBER, bold=True).next_to(bridge, RIGHT, buff=0.3)
        self.play(FadeIn(hem_fill), Create(hem), FadeIn(hem_lab), run_time=0.8)
        self.at("hem", Create(hem_mids), run_time=0.5, lead=0.4)
        self.play(Create(bridge), FadeIn(bridge_lab, shift=0.1 * RIGHT), run_time=0.7)

        # Right: round dent seen from the top
        ang = np.linspace(0, 2 * PI, 9)[:-1] + 0.2
        poly = Polygon(*[np.array([1.9 + 0.8 * np.cos(a), 0.6 + 0.8 * np.sin(a), 0]) for a in ang],
                       color=CORAL, stroke_width=6)
        circ = Circle(radius=0.8, color=CYAN, stroke_width=6).move_to([5.3, 0.6, 0])
        top_lab = txt("Round dent, top view", 34, MUTED).move_to([3.6, 2.0, 0])
        old_lab = txt("Old: polygon", 32, CORAL).next_to(poly, DOWN, buff=0.35)
        new_lab = txt(self.opts.get("new_label", "Validator: stays round"), 32, CYAN).next_to(circ, DOWN, buff=0.35)
        self.at("dent", FadeIn(top_lab), Create(poly), FadeIn(old_lab), run_time=0.7)
        self.play(Create(circ), FadeIn(new_lab), run_time=0.7)

        # --- Beat E: check every outer face against the result ----------------
        shapes = VGroup(hem, hem_fill, hem_mids, bridge, hem_lab, bridge_lab, poly, circ, top_lab, old_lab, new_lab)
        new_head = self.heading("4  Check every face", CYAN)
        p_top = Line([-6.4, 1.0, 0], [6.4, 1.0, 0]).set_stroke(WHITE, 4)
        p_bot = Line([-6.4, 0.4, 0], [6.4, 0.4, 0]).set_stroke(WHITE, 4, opacity=0.3)
        p_fill = Rectangle(width=12.8, height=0.6).move_to([0, 0.7, 0]).set_stroke(width=0).set_fill(STEEL, 0.12)
        gap_x = (2.3, 3.5)
        mids = VGroup(Line([-6.4, 0.7, 0], [gap_x[0], 0.7, 0]), Line([gap_x[1], 0.7, 0], [6.4, 0.7, 0])).set_stroke(CYAN, 7)
        self.at("probe", Transform(head, new_head), FadeOut(shapes), FadeIn(p_fill), FadeIn(p_top), FadeIn(p_bot),
                Create(mids), run_time=0.8)
        px = np.arange(-5.9, 6.0, 0.9)
        rays, marks = VGroup(), VGroup()
        for x in px:
            rays.add(Line([x, 1.0, 0], [x, 0.72, 0]).set_stroke(AMBER, 4))
            miss = gap_x[0] < x < gap_x[1]
            marks.add(Cross(scale_factor=0.13, stroke_color=CORAL, stroke_width=5).move_to([x, 0.7, 0]) if miss
                      else Dot([x, 0.7, 0], radius=0.07, color=CYAN))
        self.play(LaggedStart(*[Create(r) for r in rays], lag_ratio=0.1), run_time=1.4)
        self.play(LaggedStart(*[FadeIn(m, scale=0.6) for m in marks], lag_ratio=0.08), run_time=1.0)
        hole = Rectangle(width=gap_x[1] - gap_x[0], height=0.6).move_to([sum(gap_x) / 2, 0.7, 0])
        hole.set_stroke(CORAL, 4).set_fill(CORAL, 0.25)
        self.play(FadeIn(hole), run_time=0.5)
        badge_txt = txt("More than 0.3 % missing  →  review", 40, CORAL, bold=True)
        badge = VGroup(RoundedRectangle(corner_radius=0.15, width=badge_txt.width + 0.7, height=0.95)
                       .set_stroke(CORAL, 3).set_fill(NAVY, 0.9), badge_txt).move_to([0.0, 2.2, 0])
        self.at("review", FadeIn(badge, shift=0.15 * UP), run_time=0.5, lead=0.3)
        self.finish()


# Backward-compatible scene aliases for local custom scripts
WhyMidsurfaceScene = ThinShellScene
MidsurfaceMechanismScene = OffsetMechanismScene
