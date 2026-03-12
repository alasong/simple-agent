"""Templates module - Load agent templates from YAML files

Provides easy-to-use templates for creating new agents.
Supports base templates and scenario-specific templates.

Usage:
    from customization.templates import loader

    # List all available templates
    templates = loader.list_templates()

    # Load a template
    config = loader.load_template("developer")

    # CreateAgentCommand uses templates to generate new agents
"""
from .loader import (
    list_templates,
    load_template,
    load_template_by_path,
    get_template_path,
    create_agent_from_template,
    get_template_dir,
)

__all__ = [
    'list_templates',
    'load_template',
    'load_template_by_path',
    'get_template_path',
    'create_agent_from_template',
    'get_template_dir',
]
