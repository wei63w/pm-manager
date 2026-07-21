#!/usr/bin/env python3
"""Backward-compatible wrapper — prefer: pm init <path> """
from __future__ import annotations

import argparse
from pathlib import Path

from pm_manager_cli.scaffold import scaffold


def main() -> None:
    parser = argparse.ArgumentParser(description="Create .pm governance scaffold")
    parser.add_argument("project_root", nargs="?", default=".", help="Target project root")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    pm = scaffold(root)
    print(f"scaffolded {pm}")
    print("tip: use `pm init` for scaffold + agent install")


if __name__ == "__main__":
    main()
