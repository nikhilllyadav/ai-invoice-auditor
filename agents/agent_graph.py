import json
from rich import print
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
    return {
        "validation_human_remarks": human_input.get('remarks'),
        "validation_human_decision": human_input.get('decision'),
    }

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
    return {
        "business_validation_human_remarks": human_input.get('remarks'),
        "business_validation_human_decision": human_input.get('decision'),
    }

def route_after_data_interrupt(state: State) -> Literal["finalize","back_to_validation"]:
    decision = state.get("validation_human_decision")
    if decision in {"accept", "reject"}:
        logger.info("Human decision at data validation forces final verdict")
        return "finalize"
    return "back_to_validation"

def route_after_business_interrupt(state: State) -> Literal["finalize","back_to_business_validation"]:
    decision = state.get("business_validation_human_decision")
    if decision in {"accept", "reject"}:
        logger.info("Human decision at business validation forces final verdict")
        return "finalize"
    return "back_to_business_validation"

def route_validation(state:State)->Literal["accept","reject","human_review"]:
    validation_ai_decision=state["validation_ai_decision"]
    if validation_ai_decision=='accept':
        logger.info("Data validation returned 'accept'")
        return "accept"
    elif validation_ai_decision=='reject':
        logger.info("Data validation returned 'reject'")
        return "reject"
    else:
        logger.info("Data validation returned 'human_review'")
        return "human_review"
    
def route_business_validation_output(state:State)->Literal["accept","reject","human_review"]:
    business_validation_ai_decision=state["business_validation_ai_decision"]
    if business_validation_ai_decision=='accept':
        logger.info("Business validation returned 'accept'")
        return "accept"
    elif business_validation_ai_decision=='reject':
        logger.info("Business validation returned 'reject'")
        return "reject"
    else:
        logger.info("Business validation returned 'human_review'")
        return "human_review"

graph=StateGraph(State)

graph.add_node("extractor", extracion_node)
graph.add_node("translation_agent", translation_agent)
graph.add_node("validation_agent", validation_agent)
graph.add_node("business_validation_agent", business_validation_agent)
graph.add_node("data_validation_interrupt_node", data_validation_interrupt_node)
graph.add_node("business_validation_interrupt_node",business_validation_interrupt_node)
graph.add_node("report_node", reporting_agent)
graph.add_node("pre_report_data_node", reporting_agent)
graph.add_node("pre_report_business_node", reporting_agent)
graph.add_node("indexing_node", indexing_agent)

graph.set_entry_point("extractor")
graph.add_edge("extractor","translation_agent")
graph.add_edge("translation_agent","validation_agent")
graph.add_conditional_edges(
    "validation_agent",
    route_validation,
    {
        "accept":"business_validation_agent",
        "reject":"report_node",
        "human_review":"pre_report_data_node"
    }
)
graph.add_edge("pre_report_data_node","data_validation_interrupt_node")
graph.add_conditional_edges(
    "data_validation_interrupt_node",
    route_after_data_interrupt,
    {
        "finalize":"report_node",
        "back_to_validation":"validation_agent"
    }
)
graph.add_conditional_edges(
    "business_validation_agent",
    route_business_validation_output,
    {
        "accept":"report_node",
        "reject":"report_node",
        "human_review":"pre_report_business_node"
    }
)
graph.add_edge("pre_report_business_node","business_validation_interrupt_node")
graph.add_conditional_edges(
    "business_validation_interrupt_node",
    route_after_business_interrupt,
    {
        "finalize":"report_node",
        "back_to_business_validation":"business_validation_agent"
    }
)
graph.add_edge("report_node", "indexing_node")
graph.set_finish_point("indexing_node")

app=graph.compile(checkpointer=memory)
# mermaid_text = app.get_graph().draw_mermaid()
# print(mermaid_text)
