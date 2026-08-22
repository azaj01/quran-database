from __future__ import annotations

import importlib.util
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> types.ModuleType:
    """Import a standalone script from scripts/ as a module."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load scripts/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
