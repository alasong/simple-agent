"""
AI Development Scene - ML extensions

Contains tools for machine learning with PyTorch, scikit-learn, etc.
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
    """Load ML development tools."""
    from simple_agent.extensions import get_tool_registry

    registry = get_tool_registry()

    # ML tools (functions)
    def create_pytorch_model(name: str, layers: list) -> str:
        """Generate a PyTorch model class."""
        layer_str = "\n    ".join(layers) or "super(MyModel, self).__init__()"
        return f'''import torch
import torch.nn as nn

class {name}(nn.Module):
    def __init__(self):
        super({name}, self).__init__()
        {layer_str}

    def forward(self, x):
        return x'''

    def create_dataset_class(name: str, features: int, samples: int) -> str:
        """Generate a PyTorch Dataset class."""
        return f'''from torch.utils.data import Dataset

class {name}(Dataset):
    def __init__(self):
        self.features = torch.randn({samples}, {features})
        self.labels = torch.randint(0, 2, ({samples},))

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]'''

    def create_training_loop(model_name: str, lr: float = 0.001) -> str:
        """Generate a training loop."""
        return f'''import torch
import torch.optim as optim

model = {model_name}()
optimizer = optim.Adam(model.parameters(), lr={lr})
criterion = nn.CrossEntropyLoss()

for epoch in range(num_epochs):
    for batch in dataloader:
        inputs, labels = batch
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()'''

    def create_evaluation_metrics(predictions: str, targets: str) -> str:
        """Generate evaluation metrics code."""
        return f'''from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

accuracy = accuracy_score({targets}, {predictions})
precision = precision_score({targets}, {predictions}, average='weighted')
recall = recall_score({targets}, {predictions}, average='weighted')
f1 = f1_score({targets}, {predictions}, average='weighted')

print(f'Accuracy: {{accuracy:.4f}}')
print(f'Precision: {{precision:.4f}}')
print(f'Recall: {{recall:.4f}}')
print(f'F1 Score: {{f1:.4f}}')'''

    # Register ML tools
    registry.register("create_pytorch_model", create_pytorch_model,
                     description="Generate a PyTorch model class")
    registry.register("create_dataset_class", create_dataset_class,
                     description="Generate a PyTorch Dataset class")
    registry.register("create_training_loop", create_training_loop,
                     description="Generate a training loop")
    registry.register("create_evaluation_metrics", create_evaluation_metrics,
                     description="Generate evaluation metrics code")

    TOOLS.extend([
        "create_pytorch_model",
        "create_dataset_class",
        "create_training_loop",
        "create_evaluation_metrics"
    ])


# Auto-load on module import
load_tools()
