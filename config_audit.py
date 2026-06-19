#!/usr/bin/env python3
"""
config_audit.py - a small network config compliance auditor.

Reads exported Cisco running-configs (plain .txt files) and checks each one
against a security baseline. Prints a per-device report plus a summary, and
exits non-zero if anything fails -- so it can later run automatically in a
CI pipeline (e.g. GitHub Actions) on every push.

Usage:
    python config_audit.py configs/
"""

import re
import sys
from pathlib import Path


# --- The baseline -----------------------------------------------------------
# Each check is a small function that takes the config text and returns
# True if the device PASSES that rule. Keeping each rule as its own function
# makes the baseline easy to read and easy to extend -- add a function,
# add a line to RULES, done.

def has_hostname(cfg):
    """A real, unique hostname is set (not the factory default)."""
    m = re.search(r"^hostname (\S+)", cfg, re.MULTILINE)
    return bool(m) and m.group(1) not in ("Switch", "Router")

def has_enable_secret(cfg):
    """The privileged-mode password uses the strong 'enable secret' form."""
    return bool(re.search(r"^enable secret ", cfg, re.MULTILINE))

def no_weak_enable_password(cfg):
    """The old, reversible 'enable password' is NOT in use."""
    return not re.search(r"^enable password ", cfg, re.MULTILINE)

def ssh_only_management(cfg):
    """Every 'transport input' on the vty lines is ssh -- no Telnet, no 'all'."""
    transports = re.findall(r"transport input (.+)", cfg)
    if not transports:
        return False  # no explicit setting = not hardened
    return all(("ssh" in t and "telnet" not in t and "all" not in t)
               for t in transports)

def vty_requires_login(cfg):
    """The vty lines actually authenticate (login local or AAA)."""
    return bool(re.search(r"login local", cfg) or
                re.search(r"login authentication", cfg))

def password_encryption_on(cfg):
    """Plaintext passwords in the config are encrypted at rest."""
    return bool(re.search(r"^service password-encryption", cfg, re.MULTILINE))


# (name shown in the report, test function, how-to-fix hint)
RULES = [
    ("Hostname set (not default)",      has_hostname,           "Set a unique hostname: hostname <NAME>"),
    ("Enable secret configured",        has_enable_secret,      "Use: enable secret <password>"),
    ("No weak 'enable password'",       no_weak_enable_password,"Remove 'enable password'; use 'enable secret'"),
    ("SSH-only mgmt (no Telnet)",       ssh_only_management,    "Under line vty: transport input ssh"),
    ("VTY requires login",              vty_requires_login,     "Under line vty: login local"),
    ("Password encryption enabled",     password_encryption_on, "Add: service password-encryption"),
]


# --- The engine -------------------------------------------------------------

def audit_file(path):
    """Run every rule against one config file; return a list of results."""
    cfg = path.read_text(errors="ignore")
    return [(name, test(cfg), hint) for name, test, hint in RULES]


def main(argv):
    if len(argv) < 2:
        print("Usage: python config_audit.py <configs_dir>")
        return 2

    cfg_dir = Path(argv[1])
    files = sorted(cfg_dir.glob("*.txt"))
    if not files:
        print(f"No .txt config files found in {cfg_dir}/")
        return 2

    total_issues = 0
    for path in files:
        results = audit_file(path)
        fails = [r for r in results if not r[1]]
        total_issues += len(fails)

        status = "PASS" if not fails else f"{len(fails)} ISSUE(S)"
        print(f"\n=== {path.name}  ->  {status} ===")
        for name, ok, hint in results:
            mark = " OK " if ok else "FAIL"
            line = f"  [{mark}] {name}"
            if not ok:
                line += f"   fix: {hint}"
            print(line)

    print("\n" + "=" * 50)
    print(f"{len(files)} device(s) checked, {total_issues} issue(s) found.")
    # Exit code 0 = all clean, 1 = issues found. Handy for automation.
    return 1 if total_issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
