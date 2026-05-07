"""Compatibility wrapper for the simulation package.

The hardware-free mock server now lives in `sandwich_bt_simulation.skill_server`.
This module keeps old imports working.
"""

from sandwich_bt_simulation.skill_server import *  # noqa: F403
from sandwich_bt_simulation.skill_server import main  # noqa: F401
