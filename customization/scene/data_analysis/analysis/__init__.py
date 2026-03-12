"""
Data Analysis Scene - Analysis extensions

Contains tools for data manipulation, cleaning, and analysis with pandas and numpy.
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
    """Load data analysis tools."""
    from simple_agent.extensions import get_tool_registry

    registry = get_tool_registry()

    # Analysis tools (functions)
    def load_csv_to_dataframe(filepath: str, **kwargs) -> str:
        """Generate code to load CSV into DataFrame."""
        return f'''import pandas as pd
df = pd.read_csv("{filepath}", **{kwargs})'''

    def clean_missing_values(df_name: str, method: str = "drop") -> str:
        """Generate code to handle missing values."""
        return f'''# Handle missing values in {df_name}
{df_name}.isnull().sum()  # Check missing values
{df_name}.dropna()  # Drop rows with missing values
# or
{df_name}.fillna({{col: 0 for col in {df_name}.columns}})  # Fill with 0'''

    def calculate_statistics(df_name: str, column: str = None) -> str:
        """Generate code to calculate statistics."""
        if column:
            return f'''{df_name}["{column}"].describe()
{df_name}["{column}"].mean()
{df_name}["{column}"].std()'''
        return f'''{df_name}.describe()
{df_name}.mean(numeric_only=True)
{df_name}.corr()'''

    def filter_dataframe(df_name: str, condition: str) -> str:
        """Generate code to filter DataFrame."""
        return f'''# Filter {df_name} where {condition}
filtered_{df_name} = {df_name}[{df_name}["{condition}"]]
# or using query
filtered_{df_name} = {df_name}.query("{condition}")'''

    def group_and_aggregate(df_name: str, group_by: str, agg_func: str = "sum") -> str:
        """Generate code for groupby and aggregation."""
        return f'''# Group by {group_by} and aggregate
grouped = {df_name}.groupby("{group_by}").{agg_func}()
# or multiple aggregations
grouped = {df_name}.groupby("{group_by}").agg({{"col1": "sum", "col2": "mean"}})'''

    # Register analysis tools
    registry.register("load_csv_to_dataframe", load_csv_to_dataframe,
                     description="Generate code to load CSV into DataFrame")
    registry.register("clean_missing_values", clean_missing_values,
                     description="Generate code to handle missing values")
    registry.register("calculate_statistics", calculate_statistics,
                     description="Generate code to calculate statistics")
    registry.register("filter_dataframe", filter_dataframe,
                     description="Generate code to filter DataFrame")
    registry.register("group_and_aggregate", group_and_aggregate,
                     description="Generate code for groupby and aggregation")

    TOOLS.extend([
        "load_csv_to_dataframe",
        "clean_missing_values",
        "calculate_statistics",
        "filter_dataframe",
        "group_and_aggregate"
    ])


# Auto-load on module import
load_tools()
