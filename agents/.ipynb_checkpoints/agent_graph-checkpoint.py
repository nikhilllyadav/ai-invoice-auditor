import json
from langgraph.graph import StateGraph
from agents.utils.graph_utils import State
from agents.extractor_agent import InvoiceExtractorAgent
from agents.translation_agent import translation_agent
from agents.validation_agent import validation_agent
from agents.business_validation_agent import business_validation_agent
from agents.reporting_agent import reporting_agent
from agents.rag_agents.indexing_agent import indexing_agent
from typing import Literal
from langgraph.types import interrupt
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

import logging
from logs.logger_module import setup_logger

# Setup the memory
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# Setup the logger
logger = setup_logger(__name__, log_file="logs/my_app.log",level=logging.DEBUG)


def extracion_node(state:State)->State:
    extractor=InvoiceExtractorAgent()
    return extractor.run(state)

def data_validation_interrupt_node(state:State)->State:
    logger.info("Reached Data Validation Interrupt Node")
    human_input=interrupt(
        {
            "message":"Please check following invoice details and give response",
            "filename":state["document_name"],
            "errors":state["validation_errors"],
        }
    )
    return {"validation_human_decision":human_input.get('decision'),"validation_human_remarks":human_input.get('remarks')}

def business_validation_interrupt_node(state:State)->State:
    logger.info("Reached Business Validation Interrupt Node")
    human_input=interrupt(
        {
            "message":"Please check following invoice details and give response",
            "filename":state["document_name"],
            "errors":state["business_validation_errors"],
            "difference percentage":state["difference_percentage"]
        }
    )
    return {"business_validation_human_decision":human_input.get('decision'), "business_validation_human_remarks":human_input.get('remarks')}

def route_validation(state:State)->Literal["accept","reject","human_review"]:
    validation_ai_decision=state["validation_ai_decision"]
    if validation_ai_decision=='accept':
        return "accept"
    elif validation_ai_decision=='reject':
        return "reject"
    else:
        return "human_review"
    
def route_business_validation_output(state:State)->Literal["interrupt","report"]:
    business_validation_ai_decision=state["business_validation_ai_decision"]
    if business_validation_ai_decision=='accept':
        return "accept"
    elif business_validation_ai_decision=='reject':
        return "reject"
    else:
        return "human_review"

graph=StateGraph(State)

graph.add_node("extractor", extracion_node)
graph.add_node("translation_agent", translation_agent)
graph.add_node("validation_agent", validation_agent)
graph.add_node("business_validation_agent", business_validation_agent)
graph.add_node("data_validation_interrupt_node", data_validation_interrupt_node)
graph.add_node("business_validation_interrupt_node",business_validation_interrupt_node)
graph.add_node("report_node", reporting_agent)
graph.add_node("indexing_node", indexing_agent)

graph.set_entry_point("extractor")
graph.add_edge("extractor","translation_agent")
graph.add_edge("translation_agent","validation_agent")
graph.add_conditional_edges(
    "validation_agent",
    route_validation,
    {
        "accept":"business_validation_agent",
        "reject":"business_validation_agent",
        "human_review":"data_validation_interrupt_node"
    }
)
graph.add_edge("data_validation_interrupt_node","validation_agent")
graph.add_conditional_edges(
    "business_validation_agent",
    route_business_validation_output,
    {
        "accept":"report_node",
        "report":"report_node",
        "human_review":"business_validation_interrupt_node"
    }
)
graph.add_edge("business_validation_interrupt_node","business_validation_agent")
graph.add_edge("report_node", "indexing_node")
graph.set_finish_point("indexing_node")

app=graph.compile(checkpointer=memory)
