"""
AI Development Scene - LLM extensions

Contains tools for Large Language Models with HuggingFace Transformers.
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
    """Load LLM development tools."""
    from simple_agent.extensions import get_tool_registry

    registry = get_tool_registry()

    # LLM tools (functions)
    def create_pipeline(task: str, model_name: str = None) -> str:
        """Generate HuggingFace pipeline code."""
        model_str = f', model="{model_name}"' if model_name else ""
        return f'''from transformers import pipeline

pipe = pipeline("{task}"{model_str})
result = pipe("Your input here")
print(result)'''

    def create_llm_model(model_name: str) -> str:
        """Generate LLM model loading code."""
        return f'''from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("{model_name}")
model = AutoModelForCausalLM.from_pretrained(
    "{model_name}",
    device_map="auto",
    trust_remote_code=True
)'''

    def create_chat_template(messages: list) -> str:
        """Generate a chat template."""
        msg_str = "\n    ".join(
            f'{{"role": "{m.get("role", "user")}", "content": "{m.get("content", "")}"}}'
            for m in messages
        )
        return f'''messages = [
    {msg_str}
]

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)'''

    def create_finetuning_script(model_name: str, max_steps: int = 1000) -> str:
        """Generate a fine-tuning script."""
        return f'''from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling
)

# Load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("{model_name}")
model = AutoModelForCausalLM.from_pretrained("{model_name}")

# Training arguments
training_args = TrainingArguments(
    output_dir="./results",
    max_steps={max_steps},
    per_device_train_batch_size=4,
    learning_rate=5e-5,
    logging_steps=100,
    save_steps=1000,
)

# Data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=False
)'''

    def create_rag_pipeline(chunk_size: int = 512) -> str:
        """Generate a RAG pipeline."""
        return f'''from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA

# Split documents
text_splitter = CharacterTextSplitter(chunk_size={chunk_size}, chunk_overlap=100)
chunks = text_splitter.split_documents(documents)

# Create embeddings
embeddings = HuggingFaceEmbeddings()

# Create vector store
vectorstore = Chroma.from_documents(chunks, embeddings)

# Create RAG chain
qa_chain = RetrievalQA.from_chain_type(
    llm=model,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)'''

    # Register LLM tools
    registry.register("create_pipeline", create_pipeline,
                     description="Generate HuggingFace pipeline code")
    registry.register("create_llm_model", create_llm_model,
                     description="Generate LLM model loading code")
    registry.register("create_chat_template", create_chat_template,
                     description="Generate a chat template")
    registry.register("create_finetuning_script", create_finetuning_script,
                     description="Generate a fine-tuning script")
    registry.register("create_rag_pipeline", create_rag_pipeline,
                     description="Generate a RAG pipeline")

    TOOLS.extend([
        "create_pipeline",
        "create_llm_model",
        "create_chat_template",
        "create_finetuning_script",
        "create_rag_pipeline"
    ])


# Auto-load on module import
load_tools()
