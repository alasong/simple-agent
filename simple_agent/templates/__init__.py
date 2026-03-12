"""Templates module - Wrapper for customization module"""
from customization.templates import *
from customization.templates.loader import (
    list_templates,
    load_template,
    load_template_by_path,
    get_template_path,
    get_template_dir,
    create_agent_from_template,
    get_template_help,
)

__all__ = [
    'list_templates',
    'load_template',
    'load_template_by_path',
    'get_template_path',
    'get_template_dir',
    'create_agent_from_template',
    'get_template_help',
]
