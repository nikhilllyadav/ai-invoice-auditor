from langchain_aws import ChatBedrockConverse
from agents.utils.graph_utils import State
from logs.logger_module import setup_logger
import logging
import json
from agents.personas.persona_utils import load_persona
import re


# Setup the logger
logger = setup_logger(__name__, log_file="logs/my_app.log",level=logging.DEBUG)

# Create LLM instance
amazon_llm = ChatBedrockConverse(
    model="amazon.nova-lite-v1:0", 
    region_name="us-east-1", 
    max_tokens=200, 
)
cohere_llm = ChatBedrockConverse(
    model="cohere.command-r-plus-v1:0", 
    region_name="us-east-1", 
    max_tokens=750, 
)

def translation_agent(state: State) -> State:
    """
    This agent identifies the language of the extracted content and 
    translates the entire content in english.
    """
    # Load the agent persona
    persona = load_persona(name="translation")

    # Translate the extracted invoice details
    response = cohere_llm.invoke(f"""
    - You are a {persona["agent"]["designation"]}. 
    - Your expertise lies in {", ".join(persona["expertise"])}
    - Your task is to {", ".join(persona["job"]["steps"])}
    - NOTE: You must preserve the exact structure of the input data, and return the exact same structure with same keys. 
            Only the content of the values should be modified.

    ### Instructions
    {" ".join(persona["instructions"])}
    You MUST always provide a translation confidence, no matter what. No empty output.

    ### Output Format
    - The output must contain only the translated version of the input data converted to JSON.
    - NOTE: The output must strictly not contain any markdown element (for example: ```json or any other prefix).

    Invoice Data: {state["extracted_content"]}
    """)
    response_content = response.content

    logger.info(f"Response content from llm is : {response_content}")

    pattern = r"(\{[\s\S]*\})"
    match = re.search(pattern, response_content)
    if match:
        response_content = match.group(1)
    
    # # For removing markdown syntax (```json) added sometimes.
    # if response_content.startswith("```json"):
    #     response_content = response_content[7:-3]

    parsed_response = json.loads(response_content)

    logger.info(f"Translated content from llm is : {parsed_response}")

    # Generate confidence score for the translation
    confidence_response = cohere_llm.invoke(f"""
    - You are an expert multilingual data analyzer.
    - You will be given two python dictionaries as input.
    - One will be the multilingual source data and other one will be its translation to english.
    - Your job is to understand both of them thoroughly, and determine whether the translated version
      reflects the exact information as given in the source document.
    - Give your confidence score on the translated version.
    - The confidence score must strictly be a floating point number in the range from 0.0 to 1.0.

    ### Output Format
    - The output must strictly contain only a floating point number representing the confidence score without any salutations.

    Original Data: {state["extracted_content"]}
    Translated Data: {parsed_response}
    """)
    confidence_score = float(confidence_response.content)

    logger.info(f"The confidence score for the translated content is: {confidence_score}")

    return {
        "status": "TRANSLATION_GENERATED", 
        "translated_content": parsed_response, 
        "translation_confidence": confidence_score, 
    }