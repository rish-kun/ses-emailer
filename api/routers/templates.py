"""
Templates API router – list and render React Email templates.
"""

import json
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import verify_token

router = APIRouter()

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


class RenderRequest(BaseModel):
    template: str


def get_bun_path() -> str:
    """Find bun executable."""
    try:
        result = subprocess.run(["which", "bun"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "bun"


@router.get("/templates", dependencies=[Depends(verify_token)])
async def list_templates():
    """List available React Email templates."""
    if not TEMPLATES_DIR.exists():
        return {"templates": []}

    templates = []
    for f in TEMPLATES_DIR.iterdir():
        if f.suffix == ".tsx" and f.name != "render.js":
            templates.append(f.stem)

    return {"templates": sorted(templates)}


@router.post("/templates/render", dependencies=[Depends(verify_token)])
async def render_template(req: RenderRequest):
    """Render a React Email template to HTML."""
    template_name = req.template

    # Validate template exists
    template_file = TEMPLATES_DIR / f"{template_name}.tsx"
    if not template_file.exists():
        raise HTTPException(
            status_code=404, detail=f"Template '{template_name}' not found"
        )

    # Check for render script
    render_script = TEMPLATES_DIR / "render.js"
    if not render_script.exists():
        raise HTTPException(
            status_code=500,
            detail="Template render script not found. Run 'bun install' in templates/ directory.",
        )

    # Check node_modules exists
    node_modules = TEMPLATES_DIR / "node_modules"
    if not node_modules.exists():
        raise HTTPException(
            status_code=500,
            detail="Dependencies not installed. Run 'bun install' in templates/ directory.",
        )

    bun_path = get_bun_path()

    try:
        result = subprocess.run(
            [bun_path, "run", str(render_script), template_name],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(TEMPLATES_DIR),
        )

        if result.returncode != 0:
            error_output = result.stderr or result.stdout
            try:
                parsed = json.loads(error_output)
                raise HTTPException(
                    status_code=500, detail=parsed.get("error", "Unknown render error")
                )
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=500, detail=f"Render error: {error_output}"
                )

        parsed = json.loads(result.stdout)
        if "error" in parsed:
            raise HTTPException(status_code=500, detail=parsed["error"])

        return {"html": parsed.get("html", "")}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Template rendering timed out")
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to parse render output: {e}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render template: {e}")
