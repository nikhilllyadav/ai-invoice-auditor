from pathlib import Path
from langchain_aws import ChatBedrockConverse
from rag_utils import RagState, llm, cohere_llm
import json
import logging
from logs.logger_module import setup_logger

logger = setup_logger(__name__, log_file="logs/my_app.log",level=logging.DEBUG)

def reflection_node(state: RagState) -> RagState:
    context = "\n\n".join(state.get("retrieved_chunks", []))
    prompt = f"""
    You are a RAG evaluation system.

    Evaluate the answer below using the RAG Triad:
    1. Relevance - Does it answer the query?
    2. Groundedness - Is it supported by the context?
    3. Context Relevance - Were the retrieved chunks useful?

    Return ONLY JSON. No explanation outside JSON.
    No preamble, no trailing punctuations and no ```json prefix.

    Schema:
    {{
    "relevance": 0.0,
    "groundedness": 0.0,
    "context_relevance": 0.0,
    "reflection": "POPULATE YOUR FEEDBACK HERE..."
    }}

    Query:
    {state['query']}

    Context:
    {context}

    Answer:
    {state.get('answer')}
    """

    response = cohere_llm.invoke(prompt)
    logger.info(f"Reflection Agent - Response, {response}")
    content = response.content.strip()
    if content.startswith("```json"):
        content = content[7:-3]
    result = json.loads(content)

    state["triad_scores"] = {
        "relevance": result["relevance"],
        "groundedness": result["groundedness"],
        "context_relevance": result["context_relevance"],
    }
    state["reflection"] = result["reflection"]
    state["status"] = "REFLECTED"
    print("reflected")
    return state

