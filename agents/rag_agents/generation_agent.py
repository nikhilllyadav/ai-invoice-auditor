from rag_utils import RagState
from langchain_aws import ChatBedrockConverse
from rag_utils import llm, cohere_llm

def generation_node(state: RagState) -> RagState:
    # context = "\n\n".join(state.get("retrieved_chunks", []))

    prompt = f"""
    You are an invoice audit assistant.

    Answer the user's question ONLY using the provided context.
    If the answer is not present in the context, say "Not enough information found in records."

    User Question:
    {state['query']}

    Context:
    {state["retrieved_data"]}

    Answer in clear, concise language.
    """

    response = cohere_llm.invoke(prompt)
    state["answer"] = response.content.strip()
    state["status"] = "GENERATED"
    print("generated")
    return state
