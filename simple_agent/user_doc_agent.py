"""
User-Document Agent Generator - Wrapper for customization module

This module provides backward compatibility by importing from customization/generators.
For the latest version, use: from customization.generators.user_doc_agent import ...
"""
import sys
from pathlib import Path

# Add customization to path
_custom_path = Path(__file__).parent.parent / "customization"
if str(_custom_path) not in sys.path:
    sys.path.insert(0, str(_custom_path))

# Import from new location
from generators.user_doc_agent import *
