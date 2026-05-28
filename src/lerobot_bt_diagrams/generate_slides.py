#!/usr/bin/env python3
"""
Clean, visual presentation slides — minimal text, maximum impact.
Each slide = one big idea + schematic visual.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import os

OUT = '/home/panda-admin/users/sben/lerobot/src/lerobot_bt_diagrams/slides'
os.makedirs(OUT, exist_ok=True)

W, H = 16, 9

PRI  = '#1A237E'
ACC  = '#FF6F00'
WHT  = '#FFFFFF'
BG   = '#FAFAFA'
DRK  = '#212121'
GRY  = '#757575'
LGRY = '#BDBDBD'
GRN  = '#2E7D32'
RED  = '#C62828'
BLU  = '#1565C0'
ORG  = '#E65100'
PUR  = '#6A1B9A'
TEL  = '#00695C'

C_CAM = '#4FC3F7'
C_VLM = '#FFB74D'
C_BRG = '#AED581'
C_CPP = '#7986CB'
C_PY  = '#BA68C8'
C_ROB = '#E57373'


def slide(bg=BG):
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set(xlim=(0, W), ylim=(0, H)); ax.set_aspect('equal'); ax.axis('off')
    fig.patch.set_facecolor(bg); ax.set_facecolor(bg)
    return fig, ax


def hdr(ax, title, sub=''):
    bar = FancyBboxPatch((0, H-1.1), W, 1.1, boxstyle='round,pad=0',
                          facecolor=PRI, edgecolor='none', zorder=9)
    ax.add_patch(bar)
    ax.axhline(y=H-1.1, xmin=0, xmax=1, color=ACC, linewidth=3, zorder=10)
    ax.text(W/2, H-0.45, title, ha='center', va='center',
            fontsize=26, fontweight='bold', color=WHT, zorder=11)
    if sub:
        ax.text(W/2, H-0.88, sub, ha='center', va='center',
                fontsize=11, color='#B0BEC5', zorder=11)


def ftr(ax, n, t=13):
    ax.text(W-0.4, 0.18, f'{n}/{t}', ha='right', va='center', fontsize=9, color=LGRY, zorder=9)


def card(ax, x, y, w, h, color, title, *lines, tsize=14, lsize=11):
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.2',
                        facecolor=color, edgecolor='none', alpha=0.13, zorder=3)
    ax.add_patch(p)
    b = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.2',
                        facecolor='none', edgecolor=color, linewidth=2, alpha=0.5, zorder=3)
    ax.add_patch(b)
    if title:
        ax.text(x+w/2, y+h-0.38, title, ha='center', va='center',
                fontsize=tsize, fontweight='bold', color=color, zorder=4)
    for i, line in enumerate(lines):
        ax.text(x+w/2, y+0.28+(len(lines)-1-i)*0.42, line,
                ha='center', va='center', fontsize=lsize, color=DRK, zorder=4)


def big(ax, x, y, num, color, size=60):
    ax.text(x, y, str(num), ha='center', va='center',
            fontsize=size, fontweight='bold', color=color, alpha=0.18, zorder=2)


def arr(ax, x1, y1, x2, y2, rad=0.0, lw=2.5):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                  mutation_scale=18, linewidth=lw, color=GRY,
                  connectionstyle=f'arc3,rad={rad}', zorder=2))


def pnt(ax, x, y, text, size=14, c=DRK):
    ax.text(x-0.3, y, '▸', ha='right', va='center', fontsize=10, color=ACC, zorder=5)
    ax.text(x, y, text, ha='left', va='center', fontsize=size, color=c, zorder=5)


def ctr(ax, x, y, text, size, c=DRK, bold=False):
    ax.text(x, y, text, ha='center', va='center', fontsize=size,
            fontweight='bold' if bold else 'normal', color=c, zorder=5)


# ═══════════════════════════════════════════════════════════════════════
# 01 — TITLE
# ═══════════════════════════════════════════════════════════════════════
def s01():
    fig, ax = slide(bg=PRI)
    ax.axhline(y=5.8, xmin=0.12, xmax=0.88, color=ACC, linewidth=3.5, zorder=2)
    ctr(ax, W/2, 7.2, 'LeRobot Behavior Tree Stack', 44, WHT, True)
    ctr(ax, W/2, 6.2, 'VLM-Verified Robot Manipulation', 22, '#B0BEC5')
    ctr(ax, W/2, 4.0, 'BT + Learned Policies + VLM =', 16, '#90A4AE')
    ctr(ax, W/2, 3.1, 'Safe, Verifiable, Autonomous Manipulation', 22, ACC, True)
    ctr(ax, W/2, 1.6, 'HSP — Istituto Italiano di Tecnologia', 12, '#78909C')
    ftr(ax, 1)
    fig.savefig(f'{OUT}/slide_01_title.png', dpi=200, bbox_inches='tight', facecolor=PRI, edgecolor='none')
    plt.close(); print('01')


# ═══════════════════════════════════════════════════════════════════════
# 02 — PROBLEM
# ═══════════════════════════════════════════════════════════════════════
def s02():
    fig, ax = slide()
    hdr(ax, 'The Challenge', 'Why robots need Behavior Trees + Vision')

    problems = [
        (C_CPP, 'FRAGILE POLICIES', 'BC policies fail silently.\nNo self-assessment capability.'),
        (C_ROB, 'COMPLEX SEQUENCES', 'Multi-step tasks need\norchestration + retry logic.'),
        (C_VLM, 'NO VISUAL FEEDBACK', 'Robot cannot see if\nthe task was done correctly.'),
    ]
    for i, (c, t, d) in enumerate(problems):
        card(ax, 0.4, 4.7-i*2.0, 6.5, 1.7, c, t, d, tsize=14, lsize=12)

    ctr(ax, 11.8, 7.0, 'OUR SOLUTION', 18, ACC, True)
    card(ax, 8.2, 3.5, 7.3, 4.2, GRN, '', '',
         '▸  Behavior Trees', '     structured task flow',
         '▸  VLM Verification', '     visual check after each step',
         '▸  Automatic Retry', '     no human needed on failure',
         tsize=0, lsize=14)
    arr(ax, 6.95, 5.5, 8.15, 5.5, lw=3)

    ftr(ax, 2)
    fig.savefig(f'{OUT}/slide_02_problem.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('02')


# ═══════════════════════════════════════════════════════════════════════
# 03 — ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════
def s03():
    fig, ax = slide()
    hdr(ax, 'System Architecture', '5 layers over ROS 2')

    layers = [
        (0.2, 5.4, 3.0, 2.2, C_CAM, 'CAMERAS', 'D415 + D405\nRealSense'),
        (3.5, 5.4, 3.0, 2.2, C_VLM, 'VLM', 'Qwen3-VL\nInference'),
        (6.8, 5.4, 3.0, 2.2, C_BRG, 'BRIDGE', 'Protocol\nTranslation'),
        (10.1, 5.4, 3.0, 2.2, C_CPP, 'BT C++', 'BehaviorTree\n.CPP'),
        (13.4, 5.4, 2.5, 2.2, C_PY, 'BT PYTHON', 'Executor +\nVerification'),
    ]
    for x, y, w, h, c, t, b in layers:
        card(ax, x, y, w, h, c, t, b, tsize=14, lsize=10)
    for i in range(4):
        arr(ax, layers[i][0]+layers[i][2]+0.05, 6.5, layers[i+1][0]-0.05, 6.5)
    for i, lbl in enumerate(['topics', 'topics', 'topics', 'Services']):
        ctr(ax, (layers[i][0]+layers[i][2]+layers[i+1][0])/2, 6.78, lbl, 8, GRY)

    card(ax, 4.5, 2.0, 7.0, 1.8, C_ROB, 'FRANKA PANDA + Robotiq Gripper',
         'observation → policy inference → action @ 10 Hz', tsize=15, lsize=11)
    arr(ax, 8.0, 5.4, 8.0, 3.8)
    ctr(ax, 8.5, 4.6, 'action', 9, GRY)
    arr(ax, 6.0, 3.0, 6.0, 5.4)
    ctr(ax, 5.4, 4.2, 'obs', 9, GRY)

    ftr(ax, 3)
    fig.savefig(f'{OUT}/slide_03_architecture.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('03')


# ═══════════════════════════════════════════════════════════════════════
# 04 — BT C++
# ═══════════════════════════════════════════════════════════════════════
def s04():
    fig, ax = slide()
    hdr(ax, 'BT C++ Runtime', 'Custom BehaviorTree.CPP nodes')

    nodes = [
        (0.4, 5.6, 3.5, 1.7, C_CPP, 'RunNamedCommandNode', 'Base async leaf\nROS2 service client'),
        (4.3, 5.6, 3.5, 1.7, BLU, 'RunRobotSkillNode', 'kind="skill"\nExecutes learned policy'),
        (8.2, 5.6, 3.5, 1.7, C_VLM, 'OpenVLMGateNode', 'kind="vlm_gate"\nOpens VLM verification'),
        (12.1, 5.6, 3.5, 1.7, TEL, 'AwaitScene / DoSkill', 'Merged: command + poll\nEliminates XML boilerplate'),
    ]
    for x, y, w, h, c, t, b in nodes:
        card(ax, x, y, w, h, c, t, b, tsize=12, lsize=10)

    items = [
        'XML-driven — no recompilation',
        'RetryUntilSuccessful with max attempts',
        'Blackboard variables for skill/gate names',
        'Groot2 real-time monitoring via ZMQ',
        'Fully ROS2-native',
    ]
    for i, item in enumerate(items):
        pnt(ax, 0.8, 3.8-i*0.6, item, size=14)

    ftr(ax, 4)
    fig.savefig(f'{OUT}/slide_04_bt_cpp.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('04')


# ═══════════════════════════════════════════════════════════════════════
# 05 — BT PYTHON
# ═══════════════════════════════════════════════════════════════════════
def s05():
    fig, ax = slide()
    hdr(ax, 'BT Python Execution', 'Policy loading + robot control + verification')

    comps = [
        (C_PY, 'SkillCommandServer', 'Hosts RunNamedCommand service endpoint'),
        (PUR, 'SkillCommandExecutor', 'Policy inference loop @ 10 Hz on the robot'),
        (C_VLM, 'VlmCheckRegistry', 'In-memory VLM state, thread-safe, per-skill'),
        (TEL, 'Observation Conditions', 'AND/OR predicates, scalar comparison ops'),
    ]
    for i, (c, t, d) in enumerate(comps):
        card(ax, 0.4, 5.8-i*1.5, 6.5, 1.25, c, t, d, tsize=12, lsize=9)

    card(ax, 7.5, 1.8, 8.0, 5.5, C_PY, '', '', tsize=0, lsize=0)
    flow = [
        ('1', 'BT C++ → RunNamedCommand'),
        ('2', 'Resolve name → config'),
        ('3', 'Load policy (cached)'),
        ('4', 'Observe → Predict → Act'),
        ('5', 'Open VLM check'),
        ('6', 'Poll GetSkillVerification'),
        ('7', 'SUCCESS → next | FAILURE → retry'),
    ]
    for i, (num, text) in enumerate(flow):
        y = 6.65-i*0.75
        c = Circle((8.0, y), 0.22, facecolor=ACC, edgecolor=WHT, linewidth=2, zorder=5)
        ax.add_patch(c)
        ctr(ax, 8.0, y, num, 10, WHT, True)
        ax.text(8.6, y, text, ha='left', va='center', fontsize=12, color=DRK, zorder=5)
        if i < 6:
            arr(ax, 8.0, y-0.25, 8.0, y-0.52, lw=1.5)

    ftr(ax, 5)
    fig.savefig(f'{OUT}/slide_05_bt_python.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('05')


# ═══════════════════════════════════════════════════════════════════════
# 06 — VLM
# ═══════════════════════════════════════════════════════════════════════
def s06():
    fig, ax = slide()
    hdr(ax, 'VLM Scene Verification', 'How the Vision Language Model validates every skill')

    steps = [
        (C_PY, 'Skill\nDone', 'Robot finishes\nmanipulation'),
        (C_CPP, 'VLM\nRequest', 'BT sends\nskill + attempt'),
        (C_BRG, 'Prompt\nNL', 'Bridge translates:\n"Did robot do X?"'),
        (C_VLM, 'VLM\nAnalyzes', 'Qwen3-VL checks\ncamera frames'),
        (C_VLM, 'Verdict', 'SUCCESS / FAILED\n/ STILL_RUNNING'),
        (GRN, 'BT\nActs', 'Continue / Retry\n/ Human Help'),
    ]
    for i, (c, t, d) in enumerate(steps):
        x = 0.2+i*2.66
        card(ax, x, 4.4, 2.4, 2.5, c, t, d, tsize=13, lsize=9)
        if i < 5:
            arr(ax, x+2.45, 5.65, x+2.66, 5.65)

    card(ax, 0.3, 1.1, 3.6, 2.2, GRN, 'SUCCESS', 'Proceed to\nnext step', tsize=14, lsize=11)
    card(ax, 4.3, 1.1, 3.6, 2.2, RED, 'FAILED', 'Retry the\nsame skill', tsize=14, lsize=11)
    card(ax, 8.3, 1.1, 3.6, 2.2, ORG, 'STILL_RUNNING', 'Keep polling...\nBT waits', tsize=14, lsize=11)
    card(ax, 12.3, 1.1, 3.6, 2.2, RED, 'ERROR', 'MANUAL\nINTERVENTION', tsize=14, lsize=11)

    ftr(ax, 6)
    fig.savefig(f'{OUT}/slide_06_vlm.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('06')


# ═══════════════════════════════════════════════════════════════════════
# 07 — BRIDGE
# ═══════════════════════════════════════════════════════════════════════
def s07():
    fig, ax = slide()
    hdr(ax, 'BT-VLM Bridge', 'Protocol translation: JSON ↔ Natural Language')

    card(ax, 0.4, 3.8, 4.5, 4.0, C_PY, 'BT PROTOCOL', '',
         'Format: JSON',
         '/lerobot_bt/vlm_request',
         '/lerobot_bt/vlm_result',
         'skill_name, attempt_id,',
         'status, message',
         tsize=16, lsize=12)

    card(ax, 5.8, 4.5, 4.4, 2.8, C_BRG, 'bt_vlm_bridge.py', '',
         'skill_name → prompt NL',
         'VLM status → BT status',
         'Thread-safe state machine',
         'Configurable ROS2 params',
         tsize=15, lsize=12)

    card(ax, 11.1, 3.8, 4.5, 4.0, C_VLM, 'VLM PROTOCOL', '',
         'Format: String',
         '/panda/vlm/request',
         '/panda/vlm/status',
         'SUCCESS, FAILED,',
         'STILL_RUNNING, ERROR',
         tsize=16, lsize=12)

    arr(ax, 4.95, 6.0, 5.75, 6.0, lw=2.5); ctr(ax, 5.35, 6.3, 'JSON', 9, GRY)
    arr(ax, 10.25, 6.0, 11.05, 6.0, lw=2.5); ctr(ax, 10.65, 6.3, 'String', 9, GRY)
    arr(ax, 11.05, 4.5, 10.25, 4.5, lw=2.5); ctr(ax, 10.65, 4.2, 'String', 9, GRY)
    arr(ax, 5.75, 4.5, 4.95, 4.5, lw=2.5); ctr(ax, 5.35, 4.2, 'JSON', 9, GRY)

    examples = [
        ('place_first_toast', '"Did the robot place the toast?"'),
        ('pick_capsule', '"Did the robot insert the capsule?"'),
        ('bag_bread', '"Did the robot put bread in the bag?"'),
    ]
    for i, (skill, prompt) in enumerate(examples):
        y = 1.5-i*0.55
        ax.text(0.6, y, skill, ha='left', va='center', fontsize=11,
                fontfamily='monospace', color=C_CPP, fontweight='bold')
        ax.text(5.0, y, '→', ha='center', va='center', fontsize=11, color=GRY)
        ax.text(5.8, y, prompt, ha='left', va='center', fontsize=11, color=DRK, style='italic')

    ftr(ax, 7)
    fig.savefig(f'{OUT}/slide_07_bridge.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('07')


# ═══════════════════════════════════════════════════════════════════════
# 08 — TASKS
# ═══════════════════════════════════════════════════════════════════════
def s08():
    fig, ax = slide()
    hdr(ax, '5 Implemented Tasks', 'End-to-end: robot skills + human collaboration + VLM gates')

    tasks = [
        (ORG, 'make_sandwich', '6 stages · 2 robot skills\n4 VLM gates · ACT'),
        ('#795548','make_coffee','5 stages · 2 robot skills\n4 VLM gates · ACT'),
        (BLU, 'items_in_drawer', 'Loop-until-complete\n1 skill (repeated) · 5 gates'),
        (GRN, 'prepare_picnic_bag', 'Alternating robot/human\n2 skills · 5 gates · SmolVLA'),
        (PUR, 'set_breakfast_table', '9 steps · 4 robot skills\n5 gates · Mixed policies'),
    ]
    for i, (c, name, desc) in enumerate(tasks):
        x = 0.2+i*3.15
        card(ax, x, 4.5, 2.95, 3.0, c, name, desc, tsize=14, lsize=11)

    card(ax, 0.4, 1.0, 15.2, 2.5, ACC, '', '',
         '  COMMON TO ALL TASKS:',
         '▸  XML BT trees with RetryUntilSuccessful  |  Configurable max attempts & timeouts',
         '▸  Human collaboration gates  |  VLM verification after EVERY skill',
         '▸  Multi-machine deployment (robot + GPU server)  |  CycloneDDS',
         tsize=0, lsize=13)

    ftr(ax, 8)
    fig.savefig(f'{OUT}/slide_08_tasks.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('08')


# ═══════════════════════════════════════════════════════════════════════
# 09 — POLICIES
# ═══════════════════════════════════════════════════════════════════════
def s09():
    fig, ax = slide()
    hdr(ax, '13+ Policy Architectures', 'Plug-and-play via YAML — switch policies without code changes')

    pols = [
        (ORG, 'ACT', 'Action Chunking Transformer', 'Primary'),
        (BLU, 'SmolVLA', 'Vision-Language Action', 'Multi-task'),
        (PUR, 'GROOT', 'General Robot Transformer', 'Large model'),
        (TEL, 'π0 / π05', 'Positional Interpolation', 'Flexible'),
        (GRN, 'Diffusion', 'Generative Action Model', 'Long horizons'),
        (RED, 'Multi-Task DiT', 'Multi-Task Diffusion', 'Generalist'),
        (C_CPP, 'SARM', 'Skill-Aware Reward', 'Demonstrations'),
        (C_VLM, 'VQBeT', 'Vector Quantized', 'Compact'),
        (C_BRG, 'TDMPC', 'Model Predictive Ctrl', 'Dynamics-aware'),
    ]
    for i, (c, name, desc, use) in enumerate(pols):
        x = 0.2+(i%3)*5.3; y = 5.6-(i//3)*2.2
        card(ax, x, y, 5.0, 1.85, c, name, f'{desc}\n{use}', tsize=12, lsize=9)

    card(ax, 0.4, 0.5, 15.2, 0.7, ACC, '',
         'Also: SAC · WallX · XVLA  |  All policies lazy-loaded, cached per skill  |  Zero overhead',
         tsize=0, lsize=11)

    ftr(ax, 9)
    fig.savefig(f'{OUT}/slide_09_policies.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('09')


# ═══════════════════════════════════════════════════════════════════════
# 10 — HARDWARE
# ═══════════════════════════════════════════════════════════════════════
def s10():
    fig, ax = slide()
    hdr(ax, 'Camera & Robot Hardware', 'RealSense + Franka Panda + multiple grippers')

    card(ax, 0.4, 5.0, 7.3, 3.0, C_CAM, 'DUAL CAMERA SYSTEM', '',
         'D415 FRONT:  1280×720 @ 30fps — wide workspace',
         'D405 WRIST:  640×480 @ 30fps — close-up manip.',
         '',
         'Each camera → TWO streams:',
         '  Full-res →  operator web viewer',
         '  Low-res (320×240) →  VLM inference',
         tsize=16, lsize=12)

    card(ax, 8.5, 5.0, 7.0, 3.0, C_ROB, 'FRANKA PANDA ARM', '',
         '7-DOF torque-controlled arm',
         'ROS2 via franka_ros2',
         'IK: Pink + Pinocchio',
         'Min-jerk trajectory planning',
         tsize=16, lsize=12)

    card(ax, 0.4, 1.5, 4.8, 2.0, C_ROB, 'Robotiq 85', 'Binary open/close\n0–0.85 m range', tsize=13, lsize=10)
    card(ax, 5.6, 1.5, 4.8, 2.0, PUR, 'X-Hand', 'Dexterous multi-finger\nTactile sensors', tsize=13, lsize=10)
    card(ax, 10.8, 1.5, 4.8, 2.0, BLU, 'Leap Hand', 'DexPilot teleop.\nAlternative gripper', tsize=13, lsize=10)

    ftr(ax, 10)
    fig.savefig(f'{OUT}/slide_10_hardware.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('10')


# ═══════════════════════════════════════════════════════════════════════
# 11 — INNOVATIONS
# ═══════════════════════════════════════════════════════════════════════
def s11():
    fig, ax = slide()
    hdr(ax, 'Key Technical Innovations', 'What makes this framework unique')

    innos = [
        (TEL,  '1', 'Merged BT Nodes', 'Command + VLM poll in single leaf\n50% less XML boilerplate'),
        (C_VLM,'2', 'VLM-as-Verifier', 'VLM only reports scene state\nClean separation from planning'),
        (C_CAM,'3', 'Dual Camera Streams', 'Full-res + low-res simultaneously\nZero kernel buffer latency'),
        (C_BRG,'4', 'Protocol Bridge', 'JSON ↔ NL translation\nExtensible skill→prompt mapping'),
        (C_PY, '5', 'Multi-Policy Backend', '13+ architectures, lazy loading\nSwitch per skill via YAML'),
        (ORG,  '6', 'Human-in-the-Loop', 'Human actions as BT gates\nWAIT_HUMAN · MANUAL_INTERVENTION'),
    ]
    for i, (c, num, title, desc) in enumerate(innos):
        x = 0.2+(i%3)*5.3; y = 5.8-(i//3)*3.5
        card(ax, x, y, 5.0, 3.0, c, title, desc, tsize=14, lsize=12)
        big(ax, x+4.2, y+2.3, num, c, 48)

    ftr(ax, 11)
    fig.savefig(f'{OUT}/slide_11_innovations.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('11')


# ═══════════════════════════════════════════════════════════════════════
# 12 — RESULTS
# ═══════════════════════════════════════════════════════════════════════
def s12():
    fig, ax = slide()
    hdr(ax, 'Results & Impact', 'Quantitative achievements')

    metrics = [
        (ORG, '5', 'Complete\nTasks'),
        (BLU, '13+', 'Policy\nArchitectures'),
        (C_VLM,'30+', 'VLM Scene\nGates'),
        (PUR, '3', 'Gripper\nOptions'),
        (C_CAM,'2', 'RealSense\nCameras'),
        (GRN, '3', 'ROS2 Service\nInterfaces'),
    ]
    for i, (c, num, label) in enumerate(metrics):
        x = 0.3+i*2.6
        card(ax, x, 4.5, 2.3, 2.5, c, '', '', tsize=0, lsize=0)
        ctr(ax, x+1.15, 6.1, num, 52, c, True)
        ctr(ax, x+1.15, 5.0, label, 14, DRK)

    impacts = ['MODULAR', 'SAFE', 'SCALABLE', 'REPRODUCIBLE', 'EXTENSIBLE']
    descs = [
        'New task = YAML + XML',
        'Every skill verified',
        'Multi-machine ROS2',
        'Version-controlled configs',
        'New policies via config',
    ]
    for i, (imp, desc) in enumerate(zip(impacts, descs)):
        x = 0.3+i*3.15
        card(ax, x, 1.0, 2.9, 2.0, ACC, imp, desc, tsize=13, lsize=10)

    ftr(ax, 12)
    fig.savefig(f'{OUT}/slide_12_results.png', dpi=200, bbox_inches='tight', facecolor=BG, edgecolor='none')
    plt.close(); print('12')


# ═══════════════════════════════════════════════════════════════════════
# 13 — END
# ═══════════════════════════════════════════════════════════════════════
def s13():
    fig, ax = slide(bg=PRI)
    ax.axhline(y=5.5, xmin=0.2, xmax=0.8, color=ACC, linewidth=3, zorder=2)
    ctr(ax, W/2, 7.5, 'Thank You', 52, WHT, True)
    ctr(ax, W/2, 6.2, 'Questions?', 24, ACC)
    ctr(ax, W/2, 4.0, 'Next Steps', 20, ACC, True)
    for i, s in enumerate([
        'Scale to more complex tasks',
        'Multi-camera VLM analysis',
        'Learned recovery behaviors',
        'Deploy on ErgoCub + mobile manipulators',
        'Open-source + publish benchmarks',
    ]):
        ctr(ax, W/2, 3.0-i*0.5, f'▸  {s}', 13, '#B0BEC5')
    ctr(ax, W/2, 0.5, 'HSP — Istituto Italiano di Tecnologia', 11, '#78909C')
    ftr(ax, 13)
    fig.savefig(f'{OUT}/slide_13_end.png', dpi=200, bbox_inches='tight', facecolor=PRI, edgecolor='none')
    plt.close(); print('13')


if __name__ == '__main__':
    for fn in [s01,s02,s03,s04,s05,s06,s07,s08,s09,s10,s11,s12,s13]:
        fn()
    print(f'\nDone! 13 slides → {OUT}/')
