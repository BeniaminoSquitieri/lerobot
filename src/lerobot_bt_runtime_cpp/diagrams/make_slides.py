"""Generate 13 PNG slides (1920x1080) for the VLM<->BT PI presentation.

Style mimics the user's reference slide:
- light cream/greenish gradient background
- dark-gray title top-left
- small dark-red bar bottom-left
- clean content boxes, no overlap
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT_DIR = Path(__file__).resolve().parent / "slides"
OUT_DIR.mkdir(exist_ok=True)

W, H = 19.20, 10.80  # inches; saved at dpi=100 -> 1920x1080

# ---- Theme ----------------------------------------------------------------
BG_TOP = "#f3f5e3"
BG_BOT = "#e6ecce"
TITLE_COLOR = "#404040"
ACCENT = "#a8341c"      # bottom-left decorative bar
BLUE = "#1d4ed8"
GREEN = "#15803d"
RED = "#b91c1c"
PURPLE = "#7c3aed"
PINK = "#db2777"
INK = "#0f172a"
SUB = "#475569"

# Box palettes
BT_FILL = "#dbeafe"
PY_FILL = "#fef3c7"
VLM_FILL = "#fee2e2"
CAM_FILL = "#ede9fe"
ROBOT_FILL = "#dcfce7"
CARD_FILL = "#ffffff"
CARD_EDGE = "#cbd5e1"


def new_slide(title: str | None = None, page: int | None = None, total: int | None = None):
    fig = plt.figure(figsize=(W, H), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_axis_off()

    # vertical gradient background
    grad = np.linspace(0, 1, 512).reshape(-1, 1)
    cmap = plt.matplotlib.colors.LinearSegmentedColormap.from_list("bg", [BG_BOT, BG_TOP])
    ax.imshow(grad, extent=(0, W, 0, H), aspect="auto", cmap=cmap, zorder=-10)

    # bottom-left decorative bar
    ax.add_patch(Rectangle((0, 0.45), 1.45, 0.40, facecolor=ACCENT, edgecolor="none", zorder=2))

    if title:
        ax.text(0.85, H - 0.95, title, fontsize=44, color=TITLE_COLOR, weight="600", family="DejaVu Sans")

    if page is not None and total is not None:
        ax.text(W - 0.4, 0.35, f"{page} / {total}", fontsize=14, color=SUB, ha="right")

    return fig, ax


def card(ax, x, y, w, h, fill=CARD_FILL, edge=CARD_EDGE, lw=1.5, radius=0.18, zorder=1):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=fill, edgecolor=edge, linewidth=lw, zorder=zorder,
    )
    ax.add_patch(box)
    return box


def arrow(ax, p1, p2, color=INK, lw=2.0, style="-", zorder=3):
    ax.add_patch(FancyArrowPatch(
        p1, p2,
        arrowstyle="-|>", mutation_scale=18,
        color=color, lw=lw, linestyle=style, zorder=zorder,
        shrinkA=2, shrinkB=2,
    ))


def save(fig, name):
    out = OUT_DIR / name
    fig.savefig(out, dpi=100, facecolor="none")
    plt.close(fig)
    print("wrote", out.name)


# ---------------------------------------------------------------------------
# Slide 1 — Title
# ---------------------------------------------------------------------------
def slide_title(p, t):
    fig = plt.figure(figsize=(W, H), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_axis_off()
    grad = np.linspace(0, 1, 512).reshape(-1, 1)
    cmap = plt.matplotlib.colors.LinearSegmentedColormap.from_list("bg", ["#0f172a", "#1d4ed8"])
    ax.imshow(grad, extent=(0, W, 0, H), aspect="auto", cmap=cmap, zorder=-10)
    ax.add_patch(Rectangle((0, 0.45), 1.45, 0.40, facecolor="#ffffff", edgecolor="none"))
    ax.text(W / 2, H / 2 + 1.4, "VLM  \u2194  Behavior Tree",
            fontsize=78, color="white", weight="bold", ha="center", va="center")
    ax.text(W / 2, H / 2 + 0.1, "A scene-gated runtime for real-robot manipulation",
            fontsize=30, color="#cbd5e1", ha="center", va="center")
    ax.text(W / 2, H / 2 - 1.4, "LeRobot BT stack  \u00b7  Multi-machine ROS 2 architecture",
            fontsize=22, color="#cbd5e1", ha="center", va="center")
    ax.text(W - 0.4, 0.35, f"{p} / {t}", fontsize=14, color="#cbd5e1", ha="right")
    save(fig, "01_title.png")


# ---------------------------------------------------------------------------
# Slide 2 — Problem
# ---------------------------------------------------------------------------
def slide_problem(p, t):
    fig, ax = new_slide("The problem", p, t)
    bullets = [
        "We need a robot that runs long, multi-step manipulation tasks on a real Panda + Robotiq.",
        "Single end-to-end policies are brittle: one bad step contaminates the whole episode.",
        "We want:",
        "    \u2022  explicit task structure (which skill, in which order, with which retries)",
        "    \u2022  visual verification that each step really happened",
        "    \u2022  graceful handling of failures and human help",
    ]
    y = H - 2.6
    for line in bullets:
        ax.text(1.0, y, ("\u2022  " + line) if not line.startswith(" ") else line,
                fontsize=24, color=INK, va="top")
        y -= 0.75

    # idea box
    card(ax, 1.0, 1.4, W - 2.0, 1.5, fill="#fff7ed", edge="#fb923c", lw=2)
    ax.text(1.4, 2.65, "Idea",
            fontsize=22, color="#9a3412", weight="bold", va="center")
    ax.text(1.4, 2.05, "Split planning (BT), execution (BC skill), and verification (VLM) into three independent components.",
            fontsize=22, color=INK, va="center")
    save(fig, "02_problem.png")


# ---------------------------------------------------------------------------
# Slide 3 — Three roles
# ---------------------------------------------------------------------------
def slide_roles(p, t):
    fig, ax = new_slide("Three roles, one contract", p, t)

    cards = [
        ("BT  \u2014  planner", BT_FILL, BLUE, [
            "BehaviorTree.CPP (C++)",
            "Owns task order, gating",
            "and retry boundaries",
            "Does not look at pixels",
        ]),
        ("BC skill  \u2014  actor", PY_FILL, "#b45309", [
            "One trained manipulation",
            "primitive at a time",
            "ACT / SmolVLA / Diffusion / \u03c00",
            "Does not pick what comes next",
        ]),
        ("VLM  \u2014  verifier", VLM_FILL, RED, [
            "Reports whether the expected",
            "scene state was reached",
            "Not a planner: never picks",
            "the next skill",
        ]),
    ]
    x = 1.0
    w = (W - 2.0 - 0.6) / 3
    for title, fill, edge, lines in cards:
        card(ax, x, 1.8, w, 6.4, fill=fill, edge=edge, lw=2.5, radius=0.25)
        ax.text(x + w / 2, 7.6, title, fontsize=22, color=edge, weight="bold", ha="center")
        yy = 6.6
        for line in lines:
            ax.text(x + 0.4, yy, "\u2022 " + line, fontsize=18, color=INK, va="top")
            yy -= 0.55
        x += w + 0.3
    # Note under cards
    ax.text(W / 2, 1.3, "Vocabulary: SUCCESS  /  FAILURE  /  RUNNING  /  WAIT_HUMAN  /  MANUAL_INTERVENTION_REQUIRED",
            fontsize=15, color=SUB, ha="center", style="italic", family="DejaVu Sans Mono")
    save(fig, "03_roles.png")


# ---------------------------------------------------------------------------
# Slide 4 — Architecture diagram (redrawn)
# ---------------------------------------------------------------------------
def slide_architecture(p, t):
    fig, ax = new_slide("Architecture  \u2014  two machines, two topics", p, t)

    # Left machine
    card(ax, 0.9, 1.2, 8.0, 7.4, fill="none", edge="#334155", lw=2.5, radius=0.3)
    ax.add_patch(Rectangle((0.9, 1.2), 8.0, 7.4, fill=False, linestyle=(0, (8, 6)),
                           edgecolor="#334155", linewidth=2.5))
    ax.text(4.9, 8.2, "ROBOT MACHINE  \u2014  IITICB001DW001",
            fontsize=18, color="#334155", weight="bold", ha="center")

    card(ax, 1.3, 6.4, 7.2, 1.5, fill=BT_FILL, edge=INK, lw=2)
    ax.text(4.9, 7.45, "Behavior Tree runner (C++)", fontsize=20, ha="center", weight="bold", color=INK)
    ax.text(4.9, 7.00, "lerobot_bt_runner  \u00b7  BehaviorTree.CPP", fontsize=15, ha="center", color=SUB)
    ax.text(4.9, 6.65, "Decides order, retries, gating", fontsize=15, ha="center", color=SUB)

    card(ax, 1.3, 4.7, 7.2, 1.5, fill=PY_FILL, edge=INK, lw=2)
    ax.text(4.9, 5.75, "Python skill server", fontsize=20, ha="center", weight="bold", color=INK)
    ax.text(4.9, 5.30, "lerobot-bt-skill-server  \u00b7  rclpy", fontsize=15, ha="center", color=SUB)
    ax.text(4.9, 4.95, "Runs BC skills, opens VLM attempts", fontsize=15, ha="center", color=SUB)

    card(ax, 1.3, 2.8, 3.4, 1.6, fill=CAM_FILL, edge=INK, lw=2)
    ax.text(3.0, 3.95, "Camera publisher", fontsize=17, ha="center", weight="bold", color=INK)
    ax.text(3.0, 3.55, "panda_camera_publisher.py", fontsize=13, ha="center", color=SUB)
    ax.text(3.0, 3.20, "RealSense \u2192 ROS 2", fontsize=13, ha="center", color=SUB)

    card(ax, 5.1, 2.8, 3.4, 1.6, fill=ROBOT_FILL, edge=INK, lw=2)
    ax.text(6.8, 3.95, "Hardware", fontsize=17, ha="center", weight="bold", color=INK)
    ax.text(6.8, 3.55, "Panda + Robotiq", fontsize=13, ha="center", color=SUB)
    ax.text(6.8, 3.20, "RealSense USB cameras", fontsize=13, ha="center", color=SUB)

    arrow(ax, (4.9, 6.4), (4.9, 6.2), color=INK)
    arrow(ax, (4.9, 6.2), (4.9, 6.4), color=INK)
    arrow(ax, (3.0, 4.7), (3.0, 4.4), color=INK)
    arrow(ax, (6.8, 4.7), (6.8, 4.4), color=INK)

    # Right machine
    card(ax, 10.3, 1.2, 8.0, 7.4, fill="none", edge="#334155", lw=2.5, radius=0.3)
    ax.add_patch(Rectangle((10.3, 1.2), 8.0, 7.4, fill=False, linestyle=(0, (8, 6)),
                           edgecolor="#334155", linewidth=2.5))
    ax.text(14.3, 8.2, "GPU SERVER  \u2014  iitbmp014srv002",
            fontsize=18, color="#334155", weight="bold", ha="center")

    card(ax, 10.7, 5.0, 7.2, 2.9, fill=VLM_FILL, edge=INK, lw=2)
    ax.text(14.3, 7.45, "VLM node (panda_vlm_live.py)", fontsize=20, ha="center", weight="bold", color=INK)
    ax.text(14.3, 6.95, "Qwen3-VL  \u00b7  CUDA inference", fontsize=15, ha="center", color=SUB)
    ax.text(14.3, 6.55, "Verifies whether the expected scene was reached", fontsize=14, ha="center", color=SUB)
    ax.text(14.3, 6.15, "Not a planner: never picks the next skill", fontsize=14, ha="center", color=SUB)
    ax.text(14.3, 5.65, "Emits  PENDING \u2192 RUNNING \u2192 SUCCESS / FAILURE", fontsize=14, ha="center", color=SUB)
    ax.text(14.3, 5.30, "(or WAIT_HUMAN / MANUAL_INTERVENTION_REQUIRED)", fontsize=14, ha="center", color=SUB)

    card(ax, 10.7, 2.8, 7.2, 1.6, fill="#fde68a", edge=INK, lw=2)
    ax.text(14.3, 3.95, "Manual verifier (optional)", fontsize=17, ha="center", weight="bold", color=INK)
    ax.text(14.3, 3.55, "Human operator publishing verdicts from CLI", fontsize=14, ha="center", color=SUB)
    ax.text(14.3, 3.20, "Same topic, same JSON payload", fontsize=14, ha="center", color=SUB)

    # Inter-machine topics: horizontal arrows in the gap with labels above/below
    # vlm_request (top, blue)
    ax.text(9.6, 6.95, "/lerobot_bt/vlm_request", fontsize=12, ha="center", color=BLUE,
            weight="bold", family="DejaVu Sans Mono")
    arrow(ax, (8.9, 6.6), (10.7, 6.6), color=BLUE, lw=3)

    # vlm_result (bottom, green)
    arrow(ax, (10.7, 5.3), (8.9, 5.3), color=GREEN, lw=3)
    ax.text(9.6, 4.95, "/lerobot_bt/vlm_result", fontsize=12, ha="center", color=GREEN,
            weight="bold", family="DejaVu Sans Mono")

    # Camera topic: routed under both machines so it never crosses the boxes
    cam_y = 1.7
    ax.plot([3.0, 3.0], [2.8, cam_y], color=PURPLE, lw=2.2, linestyle="--")
    ax.plot([3.0, 16.3], [cam_y, cam_y], color=PURPLE, lw=2.2, linestyle="--")
    arrow(ax, (16.3, cam_y), (16.3, 2.8), color=PURPLE, lw=2.2, style="--")
    ax.text(9.6, 1.42, "/panda/camera/image_raw/compressed", fontsize=12, ha="center",
            color=PURPLE, weight="bold", family="DejaVu Sans Mono",
            bbox=dict(facecolor="white", edgecolor=PURPLE, boxstyle="round,pad=0.25"))

    # Footer note
    ax.text(W / 2, 0.55, "ROS 2 Jazzy  \u00b7  CycloneDDS  \u00b7  Domain 0  \u00b7  JSON payloads on std_msgs/String",
            fontsize=14, color=SUB, ha="center", style="italic")
    save(fig, "04_architecture.png")


# ---------------------------------------------------------------------------
# Slide 5 — Why two machines
# ---------------------------------------------------------------------------
def slide_two_machines(p, t):
    fig, ax = new_slide("Why split across two machines?", p, t)

    card(ax, 1.0, 4.3, (W - 2.3) / 2, 4.0, fill=BT_FILL, edge=BLUE, lw=2.5, radius=0.25)
    ax.text(1.4, 7.85, "Robot machine  (IITICB001DW001)", fontsize=22, color=BLUE, weight="bold")
    lines = [
        "Quasi real-time loop: BT tick, BC inference,",
        "gripper, RealSense USB.",
        "Runs the BT runner + Python skill server",
        "+ camera publisher.",
    ]
    yy = 7.10
    for ln in lines:
        ax.text(1.4, yy, ln, fontsize=18, color=INK)
        yy -= 0.55

    card(ax, 1.0 + (W - 2.3) / 2 + 0.3, 4.3, (W - 2.3) / 2, 4.0,
         fill=VLM_FILL, edge=RED, lw=2.5, radius=0.25)
    ax.text(1.4 + (W - 2.3) / 2 + 0.3, 7.85, "GPU server  (iitbmp014srv002)",
            fontsize=22, color=RED, weight="bold")
    lines = [
        "Heavy VLM (Qwen3-VL) inference,",
        "decoupled from the control loop.",
        "One verifier can serve any task XML",
        "without touching the robot stack.",
    ]
    yy = 7.10
    for ln in lines:
        ax.text(1.4 + (W - 2.3) / 2 + 0.3, yy, ln, fontsize=18, color=INK)
        yy -= 0.55

    card(ax, 1.0, 1.4, W - 2.0, 2.4, fill="#fff7ed", edge="#fb923c", lw=2.5, radius=0.25)
    ax.text(1.4, 3.30, "Loose coupling",
            fontsize=22, color="#9a3412", weight="bold")
    ax.text(1.4, 2.65, "The only contract is two JSON topics. Replacing the VLM",
            fontsize=20, color=INK)
    ax.text(1.4, 2.20, "with a manual verifier is a drop-in swap.",
            fontsize=20, color=INK)
    save(fig, "05_two_machines.png")


# ---------------------------------------------------------------------------
# Slide 6 — Sequence diagram
# ---------------------------------------------------------------------------
def slide_sequence(p, t):
    fig, ax = new_slide("The standard flow (per gate or skill)", p, t)

    lanes = [
        (3.5, "BT runner (C++)", BLUE),
        (9.6, "Python skill server", "#b45309"),
        (15.7, "VLM node (GPU)", RED),
    ]
    for x, name, color in lanes:
        card(ax, x - 1.7, 8.0, 3.4, 0.7, fill=color, edge=color, lw=1, radius=0.12)
        ax.text(x, 8.35, name, fontsize=18, color="white", weight="bold", ha="center", va="center")
        ax.plot([x, x], [1.0, 8.0], color="#94a3b8", lw=1.4, linestyle=(0, (3, 5)), zorder=0)

    def step(n, x, y):
        ax.add_patch(plt.Circle((x, y), 0.18, color=INK, zorder=5))
        ax.text(x, y, str(n), color="white", fontsize=12, ha="center", va="center", weight="bold", zorder=6)

    # 1 BT internal
    step(1, 3.5, 7.5)
    card(ax, 0.8, 7.0, 5.4, 0.7, fill="white", edge=CARD_EDGE, lw=1.2)
    ax.text(1.0, 7.35, 'BT tick:  OpenVLMGate(gate_name="scene_1_ready")',
            fontsize=13, family="DejaVu Sans Mono", va="center")

    # 2 Python -> VLM
    step(2, 9.6, 6.6)
    arrow(ax, (9.6, 6.5), (15.7, 6.5), color=BLUE, lw=2.5)
    ax.text(12.65, 6.7, "publish  /lerobot_bt/vlm_request",
            fontsize=13, color=BLUE, ha="center", weight="bold", family="DejaVu Sans Mono")
    card(ax, 9.9, 5.6, 6.5, 0.85, fill="white", edge=CARD_EDGE, lw=1.2)
    ax.text(10.05, 6.25, '{ "skill_name": "scene_1_ready",', fontsize=12, family="DejaVu Sans Mono")
    ax.text(10.05, 5.95, '  "attempt_id": 42,', fontsize=12, family="DejaVu Sans Mono")
    ax.text(10.05, 5.65, '  "task": "Pick the toast upon the table." }', fontsize=12, family="DejaVu Sans Mono")

    # 3 VLM RUNNING
    step(3, 15.7, 5.0)
    arrow(ax, (15.7, 4.9), (9.6, 4.9), color=INK, lw=2.5)
    ax.text(12.65, 5.1, "publish  /lerobot_bt/vlm_result   status = RUNNING",
            fontsize=13, color=INK, ha="center", weight="bold", family="DejaVu Sans Mono")
    ax.text(12.65, 4.7, "\u201cwatching the scene, not ready to decide\u201d",
            fontsize=11, color=SUB, ha="center", style="italic")

    # 4 VLM SUCCESS
    step(4, 15.7, 4.0)
    arrow(ax, (15.7, 3.9), (9.6, 3.9), color=GREEN, lw=3)
    ax.text(12.65, 4.1, "publish  /lerobot_bt/vlm_result   status = SUCCESS",
            fontsize=13, color=GREEN, ha="center", weight="bold", family="DejaVu Sans Mono")

    # 5 BT advances
    step(5, 3.5, 3.1)
    arrow(ax, (9.6, 3.0), (3.5, 3.0), color=INK, lw=2.5)
    ax.text(6.55, 3.2, "WaitForVLMVerdict  \u2192  SUCCESS",
            fontsize=13, color=INK, ha="center", weight="bold", family="DejaVu Sans Mono")
    ax.text(6.55, 2.8, "BT moves to the next node (e.g. RunRobotSkill)",
            fontsize=11, color=SUB, ha="center", style="italic")

    # Failure branch
    ax.plot([0.5, W - 0.5], [2.3, 2.3], color="#cbd5e1", lw=1.2, linestyle=(0, (3, 3)))
    ax.text(0.8, 2.05, "Alternative branch  \u2014  FAILURE verdict",
            fontsize=13, color=RED, weight="bold")

    step("4'", 15.7, 1.7)
    arrow(ax, (15.7, 1.6), (9.6, 1.6), color=RED, lw=3)
    ax.text(12.65, 1.8, "publish  /lerobot_bt/vlm_result   status = FAILURE",
            fontsize=13, color=RED, ha="center", weight="bold", family="DejaVu Sans Mono")

    step("5'", 3.5, 1.0)
    arrow(ax, (9.6, 0.9), (3.5, 0.9), color=RED, lw=2.5)
    ax.text(6.55, 1.1, "RetryUntilSuccessful  \u2192  same BC skill is re-run",
            fontsize=13, color=RED, ha="center", weight="bold", family="DejaVu Sans Mono")

    save(fig, "06_sequence.png")


# ---------------------------------------------------------------------------
# Slide 7 — JSON payloads
# ---------------------------------------------------------------------------
def slide_payloads(p, t):
    fig, ax = new_slide("What travels on the wire", p, t)

    cw = (W - 2.4) / 2
    # request
    card(ax, 1.0, 1.5, cw, 6.7, fill="white", edge=BLUE, lw=2.5, radius=0.25)
    ax.text(1.3, 7.55, "Request  \u2014  /lerobot_bt/vlm_request",
            fontsize=20, color=BLUE, weight="bold")
    code1 = [
        "{",
        '  "skill_name": "scene_1_ready",',
        '  "attempt_id": 42,',
        '  "task": "Pick the toast upon the table."',
        "}",
    ]
    card(ax, 1.3, 4.6, cw - 0.6, 2.4, fill="#0f172a", edge="#0f172a", lw=0, radius=0.12)
    yy = 6.55
    for ln in code1:
        ax.text(1.55, yy, ln, fontsize=17, color="#e2e8f0", family="DejaVu Sans Mono")
        yy -= 0.4
    ax.text(1.3, 3.95, "Published by the Python skill server", fontsize=16, color=INK)
    ax.text(1.3, 3.50, "each time the BT opens a gate or", fontsize=16, color=INK)
    ax.text(1.3, 3.05, "finishes a skill.", fontsize=16, color=INK)

    # response
    x0 = 1.0 + cw + 0.4
    card(ax, x0, 1.5, cw, 6.7, fill="white", edge=GREEN, lw=2.5, radius=0.25)
    ax.text(x0 + 0.3, 7.55, "Result  \u2014  /lerobot_bt/vlm_result",
            fontsize=20, color=GREEN, weight="bold")
    code2 = [
        "{",
        '  "skill_name": "scene_1_ready",',
        '  "attempt_id": 42,',
        '  "status": "SUCCESS",',
        '  "message": "toast visible on table"',
        "}",
    ]
    card(ax, x0 + 0.3, 4.2, cw - 0.6, 2.8, fill="#0f172a", edge="#0f172a", lw=0, radius=0.12)
    yy = 6.55
    for ln in code2:
        ax.text(x0 + 0.55, yy, ln, fontsize=17, color="#e2e8f0", family="DejaVu Sans Mono")
        yy -= 0.4
    ax.text(x0 + 0.3, 3.55, "Published by the VLM (or a human verifier).", fontsize=16, color=INK)
    ax.text(x0 + 0.3, 3.10, "skill_name + attempt_id are echoed back", fontsize=16, color=INK)
    ax.text(x0 + 0.3, 2.65, "\u2014 that is the join key.", fontsize=16, color=INK)

    save(fig, "07_payloads.png")


# ---------------------------------------------------------------------------
# Slide 8 — Verdict states
# ---------------------------------------------------------------------------
def slide_verdicts(p, t):
    fig, ax = new_slide("Verdict vocabulary drives BT behaviour", p, t)

    def state(x, y, w, h, fill, edge, title, sub1, sub2=None, title_fs=18):
        card(ax, x, y, w, h, fill=fill, edge=edge, lw=2.5, radius=0.2)
        ax.text(x + w / 2, y + h - 0.45, title, fontsize=title_fs, weight="bold",
                ha="center", color=INK)
        ax.text(x + w / 2, y + h - 0.95, sub1, fontsize=13, ha="center", color=INK)
        if sub2:
            ax.text(x + w / 2, y + h - 1.35, sub2, fontsize=12, ha="center",
                    color=SUB, style="italic")

    # PENDING
    state(8.0, 8.3, 3.2, 1.1, "#e2e8f0", INK, "PENDING", "attempt opened, nothing to do")
    # RUNNING
    state(8.0, 6.5, 3.2, 1.1, "#fde68a", INK, "RUNNING", "VLM is processing")
    arrow(ax, (9.6, 8.3), (9.6, 7.6), color=INK)

    # SUCCESS / FAILURE / WAIT_HUMAN / MANUAL
    state(0.8, 4.3, 4.0, 1.5, "#bbf7d0", INK,
          "SUCCESS", "expected scene reached",
          "scene_i_ready, task_complete")
    state(5.2, 4.3, 4.0, 1.5, "#fecaca", INK,
          "FAILURE", "expected scene NOT reached",
          "anomaly_detected")
    state(9.8, 4.3, 4.0, 1.5, "#ddd6fe", INK,
          "WAIT_HUMAN", "human action in progress",
          "BT stays blocked")
    state(13.8, 4.3, 4.8, 1.5, "#fbcfe8", INK,
          "MANUAL_INTERVENTION_REQUIRED",
          "human must fix the scene first",
          "human_help_required",
          title_fs=14)

    # arrows from RUNNING
    arrow(ax, (8.5, 6.5), (2.8, 5.8), color=GREEN, lw=2.2)
    arrow(ax, (9.2, 6.5), (7.2, 5.8), color=RED, lw=2.2)
    arrow(ax, (10.0, 6.5), (11.8, 5.8), color=PURPLE, lw=2.2)
    arrow(ax, (10.7, 6.5), (16.2, 5.8), color=PINK, lw=2.2)

    ax.text(2.8, 3.95, "\u2192 BT advances to the next node",
            fontsize=14, color=GREEN, weight="bold", ha="center")
    ax.text(7.2, 3.95, "\u2192 RetryUntilSuccessful re-runs the skill",
            fontsize=14, color=RED, weight="bold", ha="center")
    ax.text(11.8, 3.95, "\u2192 BT waits, re-issues the check",
            fontsize=14, color=PURPLE, weight="bold", ha="center")
    ax.text(16.2, 3.95, "\u2192 BT pauses, operator is notified",
            fontsize=14, color=PINK, weight="bold", ha="center")

    # next_action mapping
    card(ax, 0.8, 0.9, 8.5, 2.6, fill="white", edge=CARD_EDGE, lw=1.5, radius=0.18)
    ax.text(1.1, 3.20, "Mapping  next_action  \u2192  status",
            fontsize=16, color=INK, weight="bold")
    rows = [
        "CONTINUE                       \u2192  SUCCESS",
        "RETRY_SKILL                    \u2192  FAILURE",
        "WAIT_HUMAN                     \u2192  WAIT_HUMAN",
        "REQUEST_MANUAL_INTERVENTION    \u2192  MANUAL_INTERVENTION_REQUIRED",
    ]
    yy = 2.70
    for r in rows:
        ax.text(1.1, yy, r, fontsize=12, family="DejaVu Sans Mono", color=INK)
        yy -= 0.35

    # required JSON
    card(ax, 9.7, 0.9, 8.9, 2.6, fill="white", edge=CARD_EDGE, lw=1.5, radius=0.18)
    ax.text(10.0, 3.20, "Minimum JSON on  /lerobot_bt/vlm_result",
            fontsize=16, color=INK, weight="bold")
    rows = [
        '{ "skill_name":  "scene_1_ready",    // REQUIRED',
        '  "attempt_id":  42,                 // REQUIRED (0 = latest)',
        '  "status":      "SUCCESS",          // REQUIRED',
        '  "message":     "scene ok" }        // optional',
    ]
    yy = 2.70
    for r in rows:
        ax.text(10.0, yy, r, fontsize=12, family="DejaVu Sans Mono", color=INK)
        yy -= 0.35

    save(fig, "08_verdicts.png")


# ---------------------------------------------------------------------------
# Slide 9 — Failure handling
# ---------------------------------------------------------------------------
def slide_failure(p, t):
    fig, ax = new_slide("Failure handling  \u2014  by design", p, t)
    items = [
        ("No hidden recovery motion.",
         "On FAILURE the BT's RetryUntilSuccessful re-runs the SAME BC skill with a fresh attempt_id."),
        ("No silent fallbacks.",
         "Unknown status strings are rejected at the bridge."),
        ("Humans are first-class.",
         "WAIT_HUMAN \u2192 BT stalls; verifier re-checks the scene."),
        ("",
         "MANUAL_INTERVENTION_REQUIRED \u2192 BT pauses, operator notified."),
        ("next_action \u21c4 status.",
         "Verifier can speak either dialect; the bridge converts."),
    ]
    y = H - 2.4
    for head, body in items:
        if head:
            ax.text(1.0, y, "\u25b8  " + head, fontsize=22, color=BLUE, weight="bold")
            ax.text(1.6, y - 0.55, body, fontsize=20, color=INK)
            y -= 1.25
        else:
            ax.text(1.6, y + 0.10, body, fontsize=20, color=INK)
            y -= 0.85
    save(fig, "09_failure_handling.png")


# ---------------------------------------------------------------------------
# Slide 10 — Why this design
# ---------------------------------------------------------------------------
def slide_why(p, t):
    fig, ax = new_slide("Why this design pays off", p, t)
    cards = [
        ("Debuggable", "Every tick, gate and verdict is a logged ROS 2 message  \u2014  full replay from topics."),
        ("Swappable models", "Change one YAML field (policy_variant) to switch ACT \u2194 SmolVLA \u2194 \u03c00. BT XML untouched."),
        ("Reusable VLM", "The same verifier serves every task XML  \u2014  no per-task fine-tuning of the planner."),
        ("Safe by default", "Without a verdict the BT never advances  \u2014  no open-loop drift between skills."),
    ]
    cw = (W - 2.6) / 2
    ch = 3.2
    positions = [(1.0, 4.7), (1.0 + cw + 0.6, 4.7), (1.0, 1.2), (1.0 + cw + 0.6, 1.2)]
    for (title, body), (x, y) in zip(cards, positions):
        card(ax, x, y, cw, ch, fill="white", edge=CARD_EDGE, lw=1.8, radius=0.2)
        ax.text(x + 0.4, y + ch - 0.6, title, fontsize=24, color=BLUE, weight="bold")
        # wrap manually-ish
        ax.text(x + 0.4, y + ch - 1.6, body, fontsize=18, color=INK, wrap=True)
    save(fig, "10_why.png")


# ---------------------------------------------------------------------------
# Slide 11 — Status
# ---------------------------------------------------------------------------
def slide_status(p, t):
    fig, ax = new_slide("Current status", p, t)
    bullets = [
        "BT runtime in C++ ticking real tasks on Panda + Robotiq.",
        "Python skill server orchestrating BC skills (ACT, SmolVLA, Diffusion, \u03c00 variants).",
        "Qwen3-VL verifier on the GPU server, validated end-to-end with",
        "    simulate_vlm_test.py  and  test_vlm_protocol.py.",
        "Tasks already wired:",
    ]
    y = H - 2.6
    for line in bullets:
        ax.text(1.0, y, ("\u2022  " + line) if not line.startswith(" ") else line,
                fontsize=22, color=INK)
        y -= 0.7

    rows = [
        ["make_coffee", "make_sandwich", "items_in_drawer"],
        ["set_breakfast_table", "prepare_picnic_bag"],
    ]
    for ri, row in enumerate(rows):
        widths = [0.20 * len(tk) + 0.6 for tk in row]
        total = sum(widths) + 0.4 * (len(row) - 1)
        x = (W - total) / 2
        y = 2.7 - ri * 1.0
        for tk, w in zip(row, widths):
            card(ax, x, y, w, 0.75, fill=BLUE, edge=BLUE, lw=0, radius=0.37)
            ax.text(x + w / 2, y + 0.38, tk, color="white", fontsize=15,
                    ha="center", va="center", weight="bold", family="DejaVu Sans Mono")
            x += w + 0.4
    save(fig, "11_status.png")


# ---------------------------------------------------------------------------
# Slide 12 — Next steps
# ---------------------------------------------------------------------------
def slide_next(p, t):
    fig, ax = new_slide("Next steps", p, t)
    bullets = [
        "Richer VLM scene templates (multi-object, ordinal \u201cfirst/second\u201d reasoning).",
        "Per-skill confidence thresholds  \u2192  automatic WAIT_HUMAN escalation.",
        "Dataset convention (scene_i, BC skill, scene_{i+1}) enforced at collection time.",
        "Quantitative evaluation: success rate vs. monolithic policies on the same tasks.",
    ]
    y = H - 2.8
    for line in bullets:
        ax.text(1.0, y, "\u2022  " + line, fontsize=24, color=INK)
        y -= 1.1
    save(fig, "12_next.png")


# ---------------------------------------------------------------------------
# Slide 13 — Thanks
# ---------------------------------------------------------------------------
def slide_thanks(p, t):
    fig = plt.figure(figsize=(W, H), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_axis_off()
    grad = np.linspace(0, 1, 512).reshape(-1, 1)
    cmap = plt.matplotlib.colors.LinearSegmentedColormap.from_list("bg", ["#0f172a", "#1d4ed8"])
    ax.imshow(grad, extent=(0, W, 0, H), aspect="auto", cmap=cmap, zorder=-10)
    ax.text(W / 2, H / 2 + 0.7, "Thank you", fontsize=96, color="white",
            weight="bold", ha="center", va="center")
    ax.text(W / 2, H / 2 - 0.7, "Questions?", fontsize=44, color="#cbd5e1",
            ha="center", va="center")
    ax.text(W - 0.4, 0.35, f"{p} / {t}", fontsize=14, color="#cbd5e1", ha="right")
    save(fig, "13_thanks.png")


# ---------------------------------------------------------------------------
def main():
    total = 13
    slide_title(1, total)
    slide_problem(2, total)
    slide_roles(3, total)
    slide_architecture(4, total)
    slide_two_machines(5, total)
    slide_sequence(6, total)
    slide_payloads(7, total)
    slide_verdicts(8, total)
    slide_failure(9, total)
    slide_why(10, total)
    slide_status(11, total)
    slide_next(12, total)
    slide_thanks(13, total)


if __name__ == "__main__":
    main()
