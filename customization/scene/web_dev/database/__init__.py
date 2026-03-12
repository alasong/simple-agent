"""
Web Development Scene - Database extensions

Contains tools and utilities for database operations.
"""
import sys
from pathlib import Path

# Add scene parent to path
_scene_path = Path(__file__).parent.parent.parent
if str(_scene_path) not in sys.path:
    sys.path.insert(0, str(_scene_path))

# Scene definition
EXTENSIONS = []
TOOLS = []
STRATEGIES = []
AGENTS = []


def load_tools(**config):
    """Load database tools."""
    from simple_agent.extensions import get_tool_registry

    registry = get_tool_registry()

    # Database tools (functions)
    def create_sql_query(table: str, columns: list = None, condition: str = None) -> str:
        """Create a SQL SELECT query."""
        cols = ", ".join(columns or ["*"])
        where = f" WHERE {condition}" if condition else ""
        return f"SELECT {cols} FROM {table}{where};"

    def create_mongodb_query(collection: str, filter: dict = None, projection: dict = None) -> str:
        """Create a MongoDB query."""
        filter_str = f", filter={filter}" if filter else ""
        projection_str = f", projection={projection}" if projection else ""
        return f"db.{collection}.find({{}}{filter_str}{projection_str})"

    def create_indexStatement(table: str, columns: list) -> str:
        """Create an index statement."""
        cols = "_".join(columns)
        return f"CREATE INDEX idx_{table}_{cols} ON {table} ({', '.join(columns)});"

    def generate_orm_model(name: str, fields: dict) -> str:
        """Generate an ORM model class."""
        field_str = "\n    ".join(f"{k}: {v}" for k, v in fields.items()) or "# fields"
        return f'''class {name}:
    {field_str}'''

    # Register database tools
    registry.register("create_sql_query", create_sql_query,
                     description="Create a SQL SELECT query")
    registry.register("create_mongodb_query", create_mongodb_query,
                     description="Create a MongoDB query")
    registry.register("create_index_statement", create_indexStatement,
                     description="Create an index statement")
    registry.register("generate_orm_model", generate_orm_model,
                     description="Generate an ORM model class")

    TOOLS.extend([
        "create_sql_query",
        "create_mongodb_query",
        "create_index_statement",
        "generate_orm_model"
    ])


# Auto-load on module import
load_tools()
