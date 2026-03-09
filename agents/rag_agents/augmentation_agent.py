from rag_utils import RagState
import json
from rag_utils import llm, cohere_llm
import logging
from logs.logger_module import setup_logger

logger = setup_logger(__name__, log_file="logs/my_app.log",level=logging.DEBUG)

def augmentation_node(state: RagState) -> RagState:
    prompt = f"""
    - You are an expert context reranking system.
    - Your job is to reorder the following invoice audit report chunks based on 
      relevance to the given user query.
    
    ### Output Format
    - Return ONLY JSON with reordered content.
    - No preamble, no explaination. No trailing punctuation and characters. Just a pure JSON.

    Query: {state["query"]}
    Context Chunks: {json.dumps(state["retrieved_data"], indent=2)}
    """
    response = cohere_llm.invoke(prompt).content.strip()
    logger.info(f"Result from Augumentation->{response}")
    data = json.loads(response)

    state["retrieved_data"] = data
    # state["chunk_sources"] = data["reordered_sources"]
    state["status"] = "AUGMENTED"
    
    print("augmented")
    return state

