"""
Data Analysis Scene - Visualization extensions

Contains tools for data visualization with matplotlib and seaborn.
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
    """Load data visualization tools."""
    from simple_agent.extensions import get_tool_registry

    registry = get_tool_registry()

    # Visualization tools (functions)
    def create_line_plot(x: str, y: str, title: str = None) -> str:
        """Generate code for a line plot."""
        return f'''import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(data["{x}"], data["{y}"])
plt.xlabel("{x}")
plt.ylabel("{y}")
plt.title("{title or y} vs {x}")
plt.show()'''

    def create_bar_chart(x: str, y: str, title: str = None) -> str:
        """Generate code for a bar chart."""
        return f'''import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.bar(data["{x}"], data["{y}"])
plt.xlabel("{x}")
plt.ylabel("{y}")
plt.title("{title or y} by {x}")
plt.xticks(rotation=45)
plt.show()'''

    def create_scatter_plot(x: str, y: str, hue: str = None) -> str:
        """Generate code for a scatter plot."""
        if hue:
            return f'''import seaborn as sns

sns.scatterplot(data=data, x="{x}", y="{y}", hue="{hue}")
plt.show()'''
        return f'''import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.scatter(data["{x}"], data["{y}"])
plt.xlabel("{x}")
plt.ylabel("{y}")
plt.show()'''

    def create_histogram(column: str, bins: int = 30) -> str:
        """Generate code for a histogram."""
        return f'''import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.hist(data["{column}"], bins={bins})
plt.xlabel("{column}")
plt.ylabel("Frequency")
plt.title("Distribution of {column}")
plt.show()'''

    def create_correlation_heatmap(df_name: str) -> str:
        """Generate code for a correlation heatmap."""
        return f'''import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 10))
correlation = {df_name}.corr()
sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
plt.title("Correlation Heatmap")
plt.show()'''

    # Register visualization tools
    registry.register("create_line_plot", create_line_plot,
                     description="Generate code for a line plot")
    registry.register("create_bar_chart", create_bar_chart,
                     description="Generate code for a bar chart")
    registry.register("create_scatter_plot", create_scatter_plot,
                     description="Generate code for a scatter plot")
    registry.register("create_histogram", create_histogram,
                     description="Generate code for a histogram")
    registry.register("create_correlation_heatmap", create_correlation_heatmap,
                     description="Generate code for a correlation heatmap")

    TOOLS.extend([
        "create_line_plot",
        "create_bar_chart",
        "create_scatter_plot",
        "create_histogram",
        "create_correlation_heatmap"
    ])


# Auto-load on module import
load_tools()
