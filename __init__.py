"""
Firestarter - Thermodynamic & Bushcraft Simulation Package
"""

import os
import sys
import types

__version__ = "1.0.0"

_curr_dir = os.path.dirname(os.path.abspath(__file__))
if "firestarter" not in sys.modules:
    _pkg = types.ModuleType("firestarter")
    _pkg.__path__ = [_curr_dir]
    _pkg.__file__ = os.path.join(_curr_dir, "__init__.py")
    sys.modules["firestarter"] = _pkg
if _curr_dir not in sys.path:
    sys.path.insert(0, _curr_dir)
