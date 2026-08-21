import os
import sys

from core import base

base.original_cwd = os.getcwd()

current_dir = os.path.dirname(os.path.abspath(__file__))

# Ensure root directories
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(os.path.realpath(sys.executable)))
else:
    os.chdir(current_dir)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

os.makedirs("cache", exist_ok=True)
os.makedirs("config", exist_ok=True)
os.makedirs("logs", exist_ok=True)

import cli

cli.run()
