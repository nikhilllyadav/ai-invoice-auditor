from typing import TypedDict, Any
from langchain_aws import BedrockEmbeddings, ChatBedrockConverse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
# kb_path = str(ROOT_DIR / "data" / "kb" / "faiss")
kb_path = str(ROOT_DIR / "data" / "kb" / "faiss_new")
kb_folder = Path(kb_path)
kb_folder.mkdir(parents=True, exist_ok=True)

class RagState(TypedDict):
    status: str
    # indexed_files: list[str]
    # kb_path: str
    error: str | None
    query: str
    retrieved_chunks: list[str]
    chunk_sources: list[str]
    retrieved_data: list[dict[str, Any]]
    answer : str 
    triad_scores: dict 
    reflection: str 

    
embeddings = BedrockEmbeddings(
    client=None,
    model_id="cohere.embed-english-v3",
    region_name="us-east-1"
)

llm = ChatBedrockConverse(
    model="amazon.nova-lite-v1:0", 
    region_name="us-east-1", 
    max_tokens=1000, 
)

cohere_llm = ChatBedrockConverse(
    model="cohere.command-r-plus-v1:0", 
    region_name="us-east-1", 
    max_tokens=1000, 
)
