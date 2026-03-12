"""
Scene Extensions - Load extensions by scenario

Provides pre-configured extension packages for common scenario namespaces.

Usage:
    from customization.scene import load_scene, list_scenes

    # Load all Web Development extensions
    load_scene("web_dev")
    # Tools now available: frontend, backend, database, etc.

    # List available scenes
    scenes = list_scenes()
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Scene directory
SCENE_DIR = Path(__file__).parent

def get_scene_dir() -> Path:
    """Get the scenes directory path."""
    return SCENE_DIR

def list_scenes() -> List[str]:
    """List all available scenes."""
    scenes = []
    for item in SCENE_DIR.iterdir():
        if item.is_dir() and (item / "__init__.py").exists():
            scenes.append(item.name)
    return sorted(scenes)

def load_scene(scene_name: str, **config) -> Dict[str, Any]:
    """Load all extensions for a scene."""
    result = {
        "tools": [],
        "strategies": [],
        "agents": [],
        "loaded": [],
        "errors": []
    }

    scene_path = SCENE_DIR / scene_name
    if not scene_path.exists():
        result["errors"].append(f"Scene '{scene_name}' not found")
        return result

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            f"scene_{scene_name}",
            scene_path / "__init__.py"
        )

        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            result["loaded"] = getattr(module, "EXTENSIONS", [])
            result["tools"] = getattr(module, "TOOLS", [])
            result["strategies"] = getattr(module, "STRATEGIES", [])
            result["agents"] = getattr(module, "AGENTS", [])

    except ImportError as e:
        result["errors"].append(f"Import error: {e}")
    except Exception as e:
        result["errors"].append(f"Error loading scene: {e}")

    return result

def list_all_scenes() -> Dict[str, List[str]]:
    """Get all scenes with their contents."""
    result = {}
    for scene in list_scenes():
        scene_dir = SCENE_DIR / scene
        files = [f.stem for f in scene_dir.glob("*.py") if f.name != "__init__.py"]
        result[scene] = files
    return result
