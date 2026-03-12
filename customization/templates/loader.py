"""
Template Loader - Loads agent templates from YAML files

Usage:
    from simple_agent.templates.loader import (
        list_templates,
        load_template,
        get_template_path
    )

    # List all templates
    print(list_templates())

    # Load a template
    config = load_template("developer")
    print(config["name"])
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


# Base directory for templates
# __file__ is customization/templates/loader.py
# So parent is customization/templates, which is correct
TEMPLATE_DIR = Path(__file__).parent


def _find_yaml_files(directory: Path) -> list:
    """Find YAML files in the directory."""
    yaml_files = []
    if directory.exists():
        yaml_files.extend(directory.glob("*.yaml"))
        custom_dir = directory / "custom"
        if custom_dir.exists():
            yaml_files.extend(custom_dir.glob("*.yaml"))
    return yaml_files

def get_template_dir() -> Path:
    """Get the templates directory path."""
    return TEMPLATE_DIR


def get_template_path(template_name: str) -> Optional[Path]:
    """
    Get the file path for a template by name.

    Args:
        template_name: Template name (e.g., "developer", "base")

    Returns:
        Path to the template file, or None if not found
    """
    # Try direct match first
    direct_path = get_template_dir() / f"{template_name}.yaml"
    if direct_path.exists():
        return direct_path

    # Try custom subdirectory
    custom_path = get_template_dir() / "custom" / f"{template_name}.yaml"
    if custom_path.exists():
        return custom_path

    return None


def list_templates() -> List[Dict[str, str]]:
    """
    List all available templates.

    Returns:
        List of template info dicts with 'name' and 'description' keys
    """
    templates = []

    template_dir = get_template_dir()

    # List base templates
    if template_dir.exists():
        for yaml_file in template_dir.glob("*.yaml"):
            if yaml_file.name != "_template.yaml":  # Skip hidden files
                template_info = _load_template_info(yaml_file)
                if template_info:
                    templates.append(template_info)

    # List custom templates
    custom_dir = template_dir / "custom"
    if custom_dir.exists():
        for yaml_file in custom_dir.glob("*.yaml"):
            template_info = _load_template_info(yaml_file)
            if template_info:
                templates.append(template_info)

    return templates


def _load_template_info(yaml_path: Path) -> Optional[Dict[str, str]]:
    """Load template info from a YAML file."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or not isinstance(data, dict):
            return None

        return {
            'name': data.get('name', yaml_path.stem),
            'description': data.get('description', 'No description'),
            'path': str(yaml_path),
            'base': yaml_path.parent == get_template_dir(),
        }
    except Exception:
        return None


def load_template(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Load a template by name.

    Args:
        template_name: Template name (e.g., "developer", "base")

    Returns:
        Template configuration dict, or None if not found
    """
    path = get_template_path(template_name)
    if path is None:
        return None

    return load_template_by_path(path)


def load_template_by_path(path: str) -> Optional[Dict[str, Any]]:
    """
    Load a template from a file path.

    Args:
        path: Path to the YAML template file

    Returns:
        Template configuration dict, or None if loading failed
    """
    try:
        path = Path(path)
        if not path.exists():
            return None

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data or not isinstance(data, dict):
            return None

        # Apply default values for missing fields
        defaults = {
            'system_prompt': f"你是 {data.get('name', 'Agent')}，一个专业的 AI 助手。",
            'tools': [
                'ReadFileTool',
                'WriteFileTool',
                'BashTool',
            ],
            'max_iterations': 15,
            'domains': ['general'],
            'temperature': 0.7,
            'timeout': 300,
            'collaboration': False,
            'output_format': 'text',
        }

        # Merge defaults with loaded data
        result = {**defaults, **data}

        # Ensure tools is a list
        if 'tools' in result and isinstance(result['tools'], str):
            result['tools'] = [result['tools']]

        return result

    except Exception as e:
        print(f"Error loading template from {path}: {e}")
        return None


def create_agent_from_template(
    template_name: str,
    agent_name: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new agent configuration from a template.

    Args:
        template_name: Template name to use
        agent_name: Custom agent name (optional)
        output_dir: Directory to save the new agent config (optional)

    Returns:
        New agent configuration dict, or None if failed
    """
    template = load_template(template_name)
    if template is None:
        return None

    # Create new config from template
    new_config = {**template}

    # Override with custom values
    if agent_name:
        new_config['name'] = agent_name

    # Generate output path if specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename from agent name
        filename = f"{new_config['name'].lower().replace(' ', '_')}.yaml"
        output_file = output_path / filename

        # Save to file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(new_config, f, allow_unicode=True, default_flow_style=False)
            new_config['_saved_path'] = str(output_file)
        except Exception as e:
            print(f"Error saving agent config to {output_file}: {e}")

    return new_config


def get_template_help() -> str:
    """
    Get help text for available templates.

    Returns:
        Formatted help string
    """
    templates = list_templates()

    lines = [
        "",
        "可用模板:",
        "  基础模板:",
    ]

    for t in templates:
        indent = "    " if t.get('base', True) else "    "
        lines.append(f"{indent}- {t['name']}: {t['description']}")

    lines.extend([
        "",
        "使用方法:",
        "  python cli.py --create-agent <name> --template <template_name>",
        "",
        "示例:",
        "  python cli.py --create-agent my_dev --template developer",
        "  python cli.py --create-agent my_analyst --template analyst",
        "",
    ])

    return "\n".join(lines)
