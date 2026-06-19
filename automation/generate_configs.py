#!/usr/bin/env python3
"""
generate_configs.py - render device configs from a data model + a template.

"Infrastructure as code" for network gear:
  - the DATA (each switch's hostname, VLANs, ports, IPs) lives in devices.yml
  - the SHAPE of a config lives once in templates/access_switch.j2
  - this script combines them into one config file per device.

Add a switch = add a YAML block. You never touch the template, so every
device is built identically with no copy-paste drift.

Usage:
    pip install pyyaml jinja2
    python generate_configs.py
"""

import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

DATA_FILE = "devices.yml"
TEMPLATE_DIR = "templates"
TEMPLATE_NAME = "access_switch.j2"
OUTPUT_DIR = "generated"


def main():
    # 1. Load the data model.
    try:
        data = yaml.safe_load(Path(DATA_FILE).read_text())
    except FileNotFoundError:
        print(f"Could not find {DATA_FILE}. Run this from the project folder.")
        return 2

    common = data.get("common", {})
    switches = data.get("switches", [])
    if not switches:
        print("No switches defined in devices.yml.")
        return 2

    # 2. Set up Jinja2. trim_blocks/lstrip_blocks keep the rendered config tidy.
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(TEMPLATE_NAME)

    # 3. Render one config per device.
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(exist_ok=True)

    for device in switches:
        config_text = template.render(device=device, common=common)
        out_path = out_dir / f"{device['hostname']}.txt"
        out_path.write_text(config_text)
        print(f"  generated {out_path}")

    print(f"\nDone - {len(switches)} config(s) written to {OUTPUT_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
