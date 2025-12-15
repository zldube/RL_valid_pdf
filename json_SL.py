
# json_SL.py
# Simple JSON load/save helpers used across the pipeline.

from pathlib import Path
import json
from typing import Any, Optional


def load_json(path: str | Path) -> Optional[dict]:
    # Return parsed JSON dict if the file exists; otherwise None.
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj: Any, path: str | Path) -> Path:
    # Write obj to path as pretty JSON. Creates parents. Overwrites existing file.
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
   
