#!/usr/bin/env python3

import os
import subprocess
import glob

python_files = []
for filename in glob.iglob('PokeFacts/**/*.py', recursive=True):
    python_files.append(filename)

script_dir = os.path.dirname(os.path.abspath(__file__))
print("# Directory", script_dir)


def run_command(cmd):
    print("# Running:", cmd)
    subprocess.call(
        cmd,
        shell=True,
        cwd=script_dir)


if any(python_files):
    run_command("python -m pyflakes " + (" ".join(python_files)))
run_command("python -m pytest -v")
