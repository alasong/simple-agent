"""
Config Validation - Validate YAML configurations using JSON Schema

Provides validation utilities for agent and extension configuration files.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import yaml
from jsonschema import validate, ValidationError


# Schema directory
SCHEMA_DIR = Path(__file__).parent.parent / "configs" / "schemas"


def get_schema_path(name: str) -> Optional[Path]:
    """Get the path to a schema file by name."""
    if not name.endswith(".json"):
        name = name + ".json"
    return SCHEMA_DIR / name


def load_schema(name: str) -> Optional[Dict[str, Any]]:
    """Load a JSON schema by name."""
    schema_path = get_schema_path(name)
    if schema_path and schema_path.exists():
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def load_yaml_config(path: str) -> Optional[Dict[str, Any]]:
    """Load a YAML configuration file."""
    try:
        path = Path(path)
        if not path.exists():
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def validate_agent_config(config_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate an agent configuration file against the agent schema.

    Args:
        config_path: Path to the agent YAML file

    Returns:
        Tuple of (is_valid, list of errors)
    """
    config = load_yaml_config(config_path)
    if config is None:
        return False, [f"Could not load config file: {config_path}"]

    schema = load_schema("agent_schema")
    if schema is None:
        return False, ["Agent schema not found"]

    errors = []

    try:
        validate(instance=config, schema=schema)
    except ValidationError as e:
        errors.append({
            "type": "validation_error",
            "message": e.message,
            "path": list(e.path),
            "validator": e.validator
        })

    # Additional custom validations
    # Check that tools list is not empty
    if not config.get("tools") or len(config.get("tools", [])) == 0:
        errors.append({
            "type": "custom",
            "message": "Tools list must not be empty",
            "path": ["tools"]
        })

    # Check that domains list is not empty
    if not config.get("domains") or len(config.get("domains", [])) == 0:
        errors.append({
            "type": "custom",
            "message": "Domains list must not be empty",
            "path": ["domains"]
        })

    # Check version format
    version = config.get("version", "")
    import re
    if not re.match(r'^\d+\.\d+\.\d+$', str(version)):
        errors.append({
            "type": "custom",
            "message": "Version must be in semver format (e.g., 1.0.0)",
            "path": ["version"]
        })

    # Check max_iterations range
    max_iter = config.get("max_iterations", 15)
    if not isinstance(max_iter, int) or max_iter < 1 or max_iter > 1000:
        errors.append({
            "type": "custom",
            "message": "max_iterations must be an integer between 1 and 1000",
            "path": ["max_iterations"]
        })

    # Check temperature range
    temp = config.get("temperature", 0.7)
    if not isinstance(temp, (int, float)) or temp < 0 or temp > 1:
        errors.append({
            "type": "custom",
            "message": "temperature must be a number between 0 and 1",
            "path": ["temperature"]
        })

    # Check output_format
    output_format = config.get("output_format", "text")
    valid_formats = ["text", "code", "markdown"]
    if output_format not in valid_formats:
        errors.append({
            "type": "custom",
            "message": f"output_format must be one of {valid_formats}",
            "path": ["output_format"]
        })

    return len(errors) == 0, errors


def validate_extension_config(config_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate an extension configuration file against the extension schema.

    Args:
        config_path: Path to the extension YAML file

    Returns:
        Tuple of (is_valid, list of errors)
    """
    config = load_yaml_config(config_path)
    if config is None:
        return False, [f"Could not load config file: {config_path}"]

    schema = load_schema("extension_schema")
    if schema is None:
        return False, ["Extension schema not found"]

    errors = []

    try:
        validate(instance=config, schema=schema)
    except ValidationError as e:
        errors.append({
            "type": "validation_error",
            "message": e.message,
            "path": list(e.path),
            "validator": e.validator
        })

    return len(errors) == 0, errors


def validate_config(config_path: str, config_type: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate a configuration file with auto-detection of type.

    Args:
        config_path: Path to the YAML configuration file
        config_type: Optional explicit type ('agent' or 'extension')

    Returns:
        Tuple of (is_valid, list of errors)
    """
    config = load_yaml_config(config_path)
    if config is None:
        return False, [f"Could not load config file: {config_path}"]

    # Auto-detect config type
    if config_type is None:
        if "tools" in config and "domains" in config:
            config_type = "agent"
        elif "type" in config and "path" in config:
            config_type = "extension"
        else:
            # Try agent first
            config_type = "agent"

    if config_type == "agent":
        return validate_agent_config(config_path)
    elif config_type == "extension":
        return validate_extension_config(config_path)
    else:
        return False, [f"Unknown config type: {config_type}"]


def find_invalid_configs(directory: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Find all invalid configuration files in a directory.

    Args:
        directory: Directory to search for YAML files

    Returns:
        Dict mapping file paths to list of errors
    """
    results = {}
    yaml_files = []

    dir_path = Path(directory)
    if dir_path.exists():
        yaml_files.extend(dir_path.glob("**/*.yaml"))
        yaml_files.extend(dir_path.glob("**/*.yml"))

    for yaml_file in yaml_files:
        is_valid, errors = validate_config(str(yaml_file))
        if not is_valid:
            results[str(yaml_file)] = errors

    return results


def generate_empty_config(config_type: str = "agent", **kwargs) -> Dict[str, Any]:
    """
    Generate an empty configuration template.

    Args:
        config_type: Type of config to generate ('agent' or 'extension')
        **kwargs: Values to set in the template

    Returns:
        Configuration dictionary
    """
    if config_type == "agent":
        template = {
            "name": kwargs.get("name", "MyAgent"),
            "version": kwargs.get("version", "1.0.0"),
            "description": kwargs.get("description", "Describe your agent here"),
            "system_prompt": kwargs.get("system_prompt", "You are a helpful assistant."),
            "tools": kwargs.get("tools", ["ReadFileTool", "WriteFileTool", "BashTool"]),
            "domains": kwargs.get("domains", ["general"]),
            "max_iterations": kwargs.get("max_iterations", 15),
            "temperature": kwargs.get("temperature", 0.7),
            "timeout": kwargs.get("timeout", 300),
            "capabilities": kwargs.get("capabilities", []),
            "collaboration": kwargs.get("collaboration", False),
            "output_format": kwargs.get("output_format", "text")
        }
    elif config_type == "extension":
        template = {
            "name": kwargs.get("name", "MyExtension"),
            "type": kwargs.get("type", "tool"),
            "path": kwargs.get("path", "path/to/extension.py"),
            "enabled": kwargs.get("enabled", True),
            "description": kwargs.get("description", ""),
            "config": kwargs.get("config", {}),
            "tags": kwargs.get("tags", []),
            "dependencies": kwargs.get("dependencies", [])
        }
    else:
        template = {}

    return template


def generate_config_file(config_type: str = "agent", output_path: str = None, **kwargs) -> Optional[str]:
    """
    Generate and save a configuration file.

    Args:
        config_type: Type of config to generate
        output_path: Path to save the config file
        **kwargs: Values to set in the template

    Returns:
        Path to the generated file, or None if failed
    """
    config = generate_empty_config(config_type, **kwargs)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

        return str(output_path)

    return None


def get_validation_status(config_path: str) -> Dict[str, Any]:
    """
    Get detailed validation status for a configuration file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Status dictionary with validation results
    """
    config = load_yaml_config(config_path)
    if config is None:
        return {
            "valid": False,
            "errors": [f"Could not load config file: {config_path}"],
            "config_type": None
        }

    is_valid, errors = validate_config(config_path)

    return {
        "valid": is_valid,
        "errors": errors,
        "error_count": len(errors),
        "config_type": detect_config_type(config),
        "file_path": config_path,
        "file_exists": os.path.exists(config_path),
        "timestamp": datetime.now().isoformat()
    }


def detect_config_type(config: Dict[str, Any]) -> str:
    """Detect the type of configuration from its content."""
    if "tools" in config and "domains" in config:
        return "agent"
    elif "type" in config and "path" in config:
        return "extension"
    elif "name" in config:
        return "unknown"
    return "none"
