from agents.utils.graph_utils import State
from agents.rag_agents.rag_utils import kb_path, embeddings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
import logging
from logs.logger_module import setup_logger
import os

# Setup the logger
logger = setup_logger(__name__, log_file="logs/my_app.log",level=logging.DEBUG)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=70,
    separators=["\n\n", "\n", ". ", " "]
)

def indexing_agent(state: State) -> State:
    """
    This agent splits the invoice audit report into chunks, embeds them and stores them into teh vectorstore.
    """
    logger.info("Reached Indexing Node")
    os.makedirs(kb_path, exist_ok=True)
    report = state["audit_report"]
    invoice_metadata = state.get("extracted_meta_content")
    if not isinstance(invoice_metadata, dict):
        invoice_metadata = {}
    report_chunks = [
        Document(
            page_content=chunk, 
            metadata=invoice_metadata,
        ) for chunk in splitter.split_text(report)
    ]
    
    index_file = os.path.join(kb_path, "index.faiss")
    
    if os.path.exists(index_file):
        # Load and append
        db = FAISS.load_local(
            folder_path=kb_path, 
            embeddings=embeddings, 
            allow_dangerous_deserialization=True
        )
        db.add_documents(documents=report_chunks)
        logger.info("Updated existing vectorstore")
    else:
        # Create new from current chunks
        db = FAISS.from_documents(
            documents=report_chunks, 
            embedding=embeddings
        )
        logger.info("Created new vectorstore instance")

    # 3. Save back to local storage
    db.save_local(folder_path=kb_path)
    logger.info("Reached END of Indexing Node")

    return {
        "status": "INDEXED"
    }

