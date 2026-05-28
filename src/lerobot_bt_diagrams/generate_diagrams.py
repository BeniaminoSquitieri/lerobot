#!/usr/bin/env python3
"""
Generate clean schematic architecture diagrams for the LeRobot BT+VLM system.
Uses matplotlib to create colored box diagrams with minimal text.
No emoji -- pure schematic.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

OUT_DIR = '/home/panda-admin/users/sben/lerobot/src/lerobot_bt_diagrams'

# ── Color palette ──────────────────────────────────────────────────────
C_CAMERA   = '#4FC3F7'
C_VLM      = '#FFB74D'
C_BRIDGE   = '#AED581'
C_BT_CPP   = '#7986CB'
C_BT_PY    = '#BA68C8'
C_ROBOT    = '#E57373'
C_BG       = '#FAFAFA'
C_TEXT     = '#263238'
C_ARROW    = '#546E7A'
C_BORDER   = '#37474F'


def draw_box(ax, x, y, w, h, color, text='', text2='', fontsize=11, alpha=0.85):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle='round,pad=0.15',
        facecolor=color, edgecolor=C_BORDER,
        linewidth=1.8, alpha=alpha, zorder=3
    )
    ax.add_patch(box)
    if text:
        ax.text(x + w/2, y + h/2 + (0.08 if text2 else 0), text,
                ha='center', va='center', fontsize=fontsize, fontweight='bold',
                color=C_TEXT, zorder=4)
    if text2:
        ax.text(x + w/2, y + h/2 - 0.14, text2,
                ha='center', va='center', fontsize=fontsize-2.5,
                color=C_TEXT, zorder=4, style='italic')
    return box


def draw_arrow(ax, x1, y1, x2, y2, rad=0.0, lw=2.0):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle='-|>', mutation_scale=18,
        linewidth=lw, color=C_ARROW,
        connectionstyle=f'arc3,rad={rad}',
        zorder=2
    ))


def draw_label(ax, x, y, text, fontsize=9, color=C_TEXT, ha='center',
               rotation=0, style='normal', weight='normal'):
    ax.text(x, y, text, ha=ha, va='center', fontsize=fontsize,
            color=color, style=style, rotation=rotation, zorder=5,
            fontweight=weight)


# ══════════════════════════════════════════════════════════════════════════
# DIAGRAM 1 -- HIGH-LEVEL ARCHITECTURE OVERVIEW
# ══════════════════════════════════════════════════════════════════════════

def diagram_overview():
    fig, ax = plt.subplots(figsize=(18, 11))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 11)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    # ── Layer boxes ─────────────────────────────────────────────────
    draw_box(ax, 0.3, 6.8, 3.4, 3.5, C_CAMERA,
             'CAMERA', 'RealSense D415 + D405')
    draw_box(ax, 4.5, 6.8, 3.4, 3.5, C_VLM,
             'VLM VERIFIER', 'Vision Language Model')
    draw_box(ax, 8.7, 6.8, 3.0, 3.5, C_BRIDGE,
             'BRIDGE', 'bt_vlm_bridge.py')
    draw_box(ax, 12.4, 6.8, 3.4, 3.5, C_BT_CPP,
             'BT RUNTIME C++', 'BehaviorTree.CPP')
    draw_box(ax, 0.3, 2.0, 15.5, 3.5, C_BT_PY,
             'BT PYTHON EXECUTION', 'server.py  |  executor.py  |  verification.py')
    draw_box(ax, 6.5, 0.3, 5.0, 1.1, C_ROBOT,
             'FRANKA PANDA ROBOT', '', fontsize=12)

    # ── Arrows ──────────────────────────────────────────────────────
    draw_arrow(ax, 3.7, 8.5, 4.5, 8.5)
    draw_label(ax, 4.1, 9.0, 'low-res\nframes', fontsize=7, color=C_ARROW)

    draw_arrow(ax, 7.9, 8.5, 8.7, 8.5)
    draw_label(ax, 8.3, 9.0, 'status', fontsize=7, color=C_ARROW)

    draw_arrow(ax, 8.7, 7.5, 7.9, 7.5)
    draw_label(ax, 8.3, 7.1, 'prompt NL', fontsize=7, color=C_ARROW)

    draw_arrow(ax, 10.2, 5.5, 9.5, 5.2, rad=-0.2)
    draw_label(ax, 9.9, 5.8, 'vlm_request', fontsize=6.5, color=C_ARROW)

    draw_arrow(ax, 9.5, 4.8, 10.2, 5.1, rad=0.2)
    draw_label(ax, 9.5, 4.3, 'vlm_result', fontsize=6.5, color=C_ARROW)

    for cx in [13.5, 14.5, 15.5]:
        draw_arrow(ax, cx, 5.5, cx, 4.5, rad=-0.15)
    draw_label(ax, 14.5, 5.05, 'ROS2\nServices (3)', fontsize=7, color=C_ARROW)

    draw_arrow(ax, 9.0, 2.0, 9.0, 1.4)
    draw_label(ax, 9.5, 1.75, 'robot\naction', fontsize=7, color=C_ARROW)

    draw_arrow(ax, 7.5, 1.4, 6.0, 2.0, rad=-0.3)
    draw_label(ax, 6.0, 1.3, 'observation', fontsize=7, color=C_ARROW, rotation=55)

    # ── Layer labels ────────────────────────────────────────────────
    draw_label(ax, 2.0, 10.0, 'CAMERA LAYER', fontsize=8, color=C_CAMERA, style='italic')
    draw_label(ax, 6.2, 10.0, 'VLM LAYER', fontsize=8, color=C_VLM, style='italic')
    draw_label(ax, 10.2, 10.0, 'BRIDGE', fontsize=8, color=C_BRIDGE, style='italic')
    draw_label(ax, 14.1, 10.0, 'BT C++ LAYER', fontsize=8, color=C_BT_CPP, style='italic')
    draw_label(ax, 8.0, 5.5, 'BT PYTHON LAYER', fontsize=8, color=C_BT_PY, style='italic')
    draw_label(ax, 9.0, 1.25, 'HARDWARE', fontsize=8, color=C_ROBOT, style='italic')

    ax.text(9, 10.8, 'LeRobot -- Architettura di Comunicazione BT + VLM',
            ha='center', va='center', fontsize=16, fontweight='bold', color=C_TEXT)

    plt.tight_layout(pad=0.5)
    fig.savefig(f'{OUT_DIR}/01_overview.png', dpi=180, bbox_inches='tight',
                facecolor=C_BG, edgecolor='none')
    plt.close()
    print('Saved: 01_overview.png')


# ══════════════════════════════════════════════════════════════════════════
# DIAGRAM 2 -- BT C++ <-> BT PYTHON (ROS2 Services Detail)
# ══════════════════════════════════════════════════════════════════════════

def diagram_bt_cpp_python():
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    draw_box(ax, 0.5, 5.5, 6.0, 4.0, C_BT_CPP,
             'BT RUNTIME C++', 'BehaviorTree.CPP + ROS2 Node')

    for name, y in [
        ('RunRobotSkillNode', 8.3), ('OpenVLMGateNode', 7.6),
        ('AwaitSceneNode', 6.9), ('DoSkillNode', 6.2)
    ]:
        draw_box(ax, 1.2, y - 0.15, 3.2, 0.55, '#5C6BC0', name, '', fontsize=9, alpha=0.7)

    draw_box(ax, 1.2, 8.8, 4.5, 0.5, '#3F51B5',
             'lerobot_bt_main.cpp + Factory', '', fontsize=9, alpha=0.6)

    draw_box(ax, 9.5, 5.5, 6.0, 4.0, C_BT_PY,
             'BT PYTHON EXECUTION', 'server.py + executor.py')

    for name, y in [
        ('SkillCommandServer', 8.5), ('SkillCommandExecutor', 7.8),
        ('VlmCheckRegistry', 7.1),
        ('Learned Policies (ACT, Diffusion, pi0, ...)', 6.4)
    ]:
        draw_box(ax, 10.2, y - 0.15, 4.8, 0.55, '#AB47BC', name, '', fontsize=9, alpha=0.7)

    services = [
        ('RunNamedCommand', 'kind, name, timeout_s  -->  success, status'),
        ('GetSkillVerification', 'skill_name  -->  attempt_id, status'),
        ('ReportSkillVerification', 'skill_name, status  -->  accepted'),
    ]
    for i, (svc_name, desc) in enumerate(services):
        sy = 8.3 - i * 0.7
        draw_box(ax, 7.0, sy - 0.12, 2.2, 0.52, '#FFF9C4', svc_name, '', fontsize=8, alpha=0.9)
        draw_label(ax, 8.1, sy - 0.35, desc, fontsize=5.8, color=C_ARROW, ha='center')
        draw_arrow(ax, 6.6, sy + 0.15, 7.0, sy + 0.15, lw=1.8)
        draw_arrow(ax, 9.2, sy + 0.35, 9.5, sy + 0.35, rad=0.05, lw=1.8)

    draw_box(ax, 5.0, 3.5, 6.0, 1.2, C_ROBOT,
             'FRANKA PANDA', 'observation --> policy --> action', fontsize=11)

    draw_arrow(ax, 11.0, 5.5, 10.0, 4.7, rad=0.2)
    draw_label(ax, 11.5, 4.8, 'robot_action', fontsize=7, color=C_ARROW)
    draw_arrow(ax, 6.0, 4.7, 7.0, 5.5, rad=0.2)
    draw_label(ax, 5.5, 4.8, 'observation', fontsize=7, color=C_ARROW)

    draw_box(ax, 0.5, 3.5, 3.5, 1.2, '#B0BEC5', 'Groot2 GUI', 'real-time BT monitor', fontsize=10)
    draw_arrow(ax, 2.3, 4.7, 2.3, 5.5, lw=1.5)
    draw_label(ax, 2.8, 5.1, 'ZMQ', fontsize=7, color=C_ARROW)

    draw_box(ax, 0.5, 1.5, 7.0, 1.5, '#ECEFF1', '', '', alpha=0.5)
    draw_label(ax, 4.0, 2.65, 'LEGENDA', fontsize=10, color=C_TEXT, weight='bold')
    draw_label(ax, 1.2, 2.1, '-->   ROS2 Service (C++ client <--> Python server)', fontsize=8, color=C_ARROW, ha='left')
    draw_label(ax, 1.2, 1.7, '      3 services: RunNamedCommand, GetSkillVerification, ReportSkillVerification', fontsize=7, color=C_ARROW, ha='left', style='italic')

    ax.text(8, 9.7, 'Comunicazione BT C++  <-->  BT Python (ROS2 Services)',
            ha='center', va='center', fontsize=16, fontweight='bold', color=C_TEXT)

    draw_label(ax, 3.5, 9.5, 'C++', fontsize=11, color=C_BT_CPP, style='italic', weight='bold')
    draw_label(ax, 12.5, 9.5, 'Python', fontsize=11, color=C_BT_PY, style='italic', weight='bold')

    plt.tight_layout(pad=0.5)
    fig.savefig(f'{OUT_DIR}/02_bt_cpp_python.png', dpi=180, bbox_inches='tight',
                facecolor=C_BG, edgecolor='none')
    plt.close()
    print('Saved: 02_bt_cpp_python.png')


# ══════════════════════════════════════════════════════════════════════════
# DIAGRAM 3 -- BT <-> VLM COMMUNICATION FLOW
# ══════════════════════════════════════════════════════════════════════════

def diagram_bt_vlm_flow():
    fig, ax = plt.subplots(figsize=(18, 10))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    draw_box(ax, 0.5, 4.5, 3.5, 4.5, C_BT_PY, 'BT PYTHON', 'server.py\nverification.py')
    draw_box(ax, 7.0, 4.5, 4.0, 4.5, C_BRIDGE, 'BT-VLM BRIDGE', 'bt_vlm_bridge.py')
    draw_box(ax, 14.0, 4.5, 3.5, 4.5, C_VLM, 'VLM VERIFIER', 'Analisi scene\nvia LLM')
    draw_box(ax, 6.0, 0.3, 6.0, 1.0, C_CAMERA, 'CAMERE (D415 + D405)', '320x240 low-res per VLM', fontsize=11)

    steps = [
        (4.2, 8.6, '1', 'BT pubblica\nvlm_request (JSON)', C_BT_PY),
        (9.2, 8.6, '2', 'Bridge traduce\nskill -> prompt NL', C_BRIDGE),
        (12.5, 8.6, '3', 'Bridge invia prompt\nal VLM Verifier', C_BRIDGE),
        (15.8, 8.6, '4', 'VLM analizza\nle immagini', C_VLM),
        (15.8, 5.5, '5', 'VLM risponde:\nSUCCESS|FAILED\n|STILL_RUNNING', C_VLM),
        (9.2, 5.5, '6', 'Bridge traduce\n-> BT status', C_BRIDGE),
        (4.2, 5.5, '7', 'Bridge pubblica\nvlm_result (JSON)', C_BT_PY),
        (2.0, 4.8, '8', 'VlmCheckRegistry\naggiorna stato', C_BT_PY),
    ]
    for x, y, num, desc, color in steps:
        ax.text(x, y, num, ha='center', va='center', fontsize=14,
                fontweight='bold', color=color, zorder=5)
        ax.text(x + 0.35, y - 0.1, desc, ha='left', va='top', fontsize=7.5,
                color=C_TEXT, zorder=5, linespacing=1.3)

    draw_arrow(ax, 4.0, 8.0, 7.0, 8.0, lw=2.2)
    draw_label(ax, 5.5, 8.45, '/lerobot_bt/vlm_request', fontsize=6.5, color=C_ARROW)

    draw_arrow(ax, 11.0, 8.0, 14.0, 8.0, lw=2.2)
    draw_label(ax, 12.5, 8.45, '/panda/vlm/request', fontsize=6.5, color=C_ARROW)

    draw_arrow(ax, 15.8, 7.5, 15.8, 6.8, lw=1.5)

    draw_arrow(ax, 14.0, 6.2, 11.0, 6.2, lw=2.2)
    draw_label(ax, 12.5, 6.65, '/panda/vlm/status', fontsize=6.5, color=C_ARROW)

    draw_arrow(ax, 7.0, 6.2, 4.0, 6.2, lw=2.2)
    draw_label(ax, 5.5, 6.65, '/lerobot_bt/vlm_result', fontsize=6.5, color=C_ARROW)

    draw_arrow(ax, 3.5, 5.5, 2.5, 5.5, lw=1.5)

    draw_arrow(ax, 9.0, 1.3, 16.0, 4.5, rad=0.35, lw=1.8)
    draw_label(ax, 13.5, 3.0, 'frame low-res 320x240', fontsize=7, color=C_ARROW)

    draw_arrow(ax, 6.0, 0.8, 1.0, 4.5, rad=-0.35, lw=1.5)
    draw_label(ax, 2.5, 2.5, 'observation', fontsize=7, color=C_ARROW)

    draw_box(ax, 7.0, 1.8, 4.0, 2.0, '#ECEFF1', '', '', alpha=0.5)
    draw_label(ax, 9.0, 3.55, 'TRADUZIONE STATUS', fontsize=8, color=C_TEXT, weight='bold')
    for i, (vlm_s, arrow_s, bt_s, c1, c2) in enumerate([
        ('SUCCESS', '->', 'SUCCESS', C_VLM, C_BT_PY),
        ('FAILED', '->', 'FAILURE', C_VLM, C_BT_PY),
        ('STILL_RUNNING', '->', 'RUNNING', C_VLM, C_BT_PY),
        ('ERROR', '->', 'MANUAL_INTERVENTION', C_VLM, C_ROBOT),
    ]):
        ty = 3.25 - i * 0.4
        ax.text(7.4, ty, 'VLM ' + vlm_s, ha='left', fontsize=6.5, color=c1, fontweight='bold')
        ax.text(9.0, ty, arrow_s, ha='center', fontsize=6.5, color=C_TEXT)
        ax.text(9.8, ty, 'BT ' + bt_s, ha='left', fontsize=6.5, color=c2, fontweight='bold')

    draw_box(ax, 0.5, 1.8, 6.0, 2.0, '#ECEFF1', '', '', alpha=0.5)
    draw_label(ax, 3.5, 3.55, 'MAPPING SKILL -> PROMPT NL', fontsize=8, color=C_TEXT, weight='bold')
    for i, (skill, arrow_s, prompt) in enumerate([
        ('place_first_toast', '->', '"Did the robot place the toast?"'),
        ('bag_bread', '->', '"Did the robot put bread in the bag?"'),
        ('make_coffee.*', '->', '"Is the coffee machine running?"'),
    ]):
        ty = 3.25 - i * 0.4
        ax.text(0.8, ty, skill, ha='left', fontsize=6.5, color=C_BT_CPP, fontfamily='monospace')
        ax.text(2.8, ty, arrow_s, ha='center', fontsize=6.5, color=C_TEXT)
        ax.text(3.4, ty, prompt, ha='left', fontsize=6.5, color=C_ARROW, style='italic')

    ax.text(9, 9.5, 'Comunicazione BT  <-->  VLM (Topic ROS2 + Bridge)',
            ha='center', va='center', fontsize=16, fontweight='bold', color=C_TEXT)

    draw_label(ax, 2.2, 9.0, 'STEP 1-2, 7-8', fontsize=7, color=C_BT_PY, style='italic')
    draw_label(ax, 9.0, 9.0, 'STEP 2-3, 5-6', fontsize=7, color=C_BRIDGE, style='italic')
    draw_label(ax, 15.8, 9.0, 'STEP 3-5', fontsize=7, color=C_VLM, style='italic')

    plt.tight_layout(pad=0.5)
    fig.savefig(f'{OUT_DIR}/03_bt_vlm_flow.png', dpi=180, bbox_inches='tight',
                facecolor=C_BG, edgecolor='none')
    plt.close()
    print('Saved: 03_bt_vlm_flow.png')


if __name__ == '__main__':
    diagram_overview()
    diagram_bt_cpp_python()
    diagram_bt_vlm_flow()
    print('Done! All 3 diagrams saved in', OUT_DIR)
