from __future__ import annotations

import json
import sys
from pathlib import Path

# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# FASTAPI APPLICATION
# ============================================================

from src.api.main import app


# ============================================================
# EXPORT OPENAPI
# ============================================================

def export_openapi_spec() -> Path:
    """
    Export the FastAPI OpenAPI specification to JSON.
    """

    spec = app.openapi()

    output_path = BASE_DIR / "openapi.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            spec,
            f,
            indent=2,
            ensure_ascii=False,
        )

    return output_path


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":

    path = export_openapi_spec()

    print(
        f"[SUCCESS] OpenAPI specification exported to:\n"
        f"{path}"
    )