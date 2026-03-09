from rag_utils import RagState
from langgraph.graph import StateGraph, END
from retrieval_agent import retrieval_node
from augmentation_agent import augmentation_node
from generation_agent import generation_node
from reflection_agent import reflection_node
from langgraph.checkpoint.memory import InMemorySaver

graph = StateGraph(RagState)

# graph.add_node("indexing", indexing_node)                 ## Now moved to processing graph
graph.add_node("retrieval", retrieval_node)
graph.add_node("augmentation", augmentation_node)
graph.add_node("generation", generation_node)
graph.add_node("reflection", reflection_node)

graph.set_entry_point("retrieval")
graph.add_edge("retrieval","generation")
# graph.add_edge("retrieval", "augmentation")
# graph.add_edge("augmentation", "generation")
graph.add_edge("generation", "reflection")
graph.add_edge("reflection", END)

rag_app = graph.compile(checkpointer=InMemorySaver())
