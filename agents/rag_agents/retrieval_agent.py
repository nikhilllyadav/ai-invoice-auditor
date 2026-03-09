from rag_utils import RagState
from langchain_community.vectorstores import FAISS
from rag_utils import embeddings, kb_path
import logging
from logs.logger_module import setup_logger

logger = setup_logger(__name__, log_file="logs/my_app.log",level=logging.DEBUG)

def retrieval_node(state: RagState) -> RagState:
    logger.info("RAG Graph--Reached Retrieval Node")
    try:
        kb = FAISS.load_local(kb_path, embeddings, allow_dangerous_deserialization=True)
        results = kb.similarity_search(state["query"], k=5)
        logger.info(f"RAG Graph--Result from KB: {results}")

        # state["retrieved_chunks"] = [r.page_content for r in results]
        # state["chunk_sources"] = [r.metadata["sender"] for r in results]
        state["retrieved_data"] = [
            {
                "chunk_content": chunk.page_content, 
                "chunk_metadata": chunk.metadata, 
            } for chunk in results
        ]
        state["status"] = "RETRIEVAL_DONE"

    except Exception as e:
        logger.error(f"RAG Graph--Retrieval Node Error: {e}")
        state["status"] = "RETRIEVAL_FAILED"
        state["error"] = str(e)

    print("retrieved")
    return state



