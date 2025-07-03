# graph.py
import os
import json
from typing import TypedDict, List
from dotenv import load_dotenv

import google.generativeai as genai
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, END

from prompts import QUESTIONS, ANSWER_MAPPING, SYSTEM_PROMPT, PARSER_PROMPT

load_dotenv()

# --- LLM and State Definition ---
# Configure the Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
llm = genai.GenerativeModel('gemini-2.5-flash-lite')

class GraphState(TypedDict):
    initial_user_data: dict
    collected_data: dict
    question_keys_to_ask: List[str]
    current_question_key: str
    user_response: str
    parsed_answer: str
    final_prediction: int
    prediction_confidence: float # New field for confidence
    conversation_history: List[str]


# --- Graph Nodes ---

def node_ask_question(state: GraphState):
    """This node's ONLY job is to ask the next question."""
    key = state['current_question_key']
    question_text = QUESTIONS[key]

    prompt = SYSTEM_PROMPT.format(question=question_text)
    response = llm.generate_content(prompt)

    return {"conversation_history": state['conversation_history'] + [f"AI: {response.text}"]}


def node_parse_response(state: GraphState):
    """Parses the user's latest response to determine if it's yes/no/unsure."""
    key = state['current_question_key']
    question_text = QUESTIONS[key]
    user_response = state['user_response']

    prompt = PARSER_PROMPT.format(
        question=question_text, user_response=user_response
    )

    response = llm.generate_content(prompt)

    try:
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(cleaned_response)
        parsed_answer = parsed_json.get("answer", "unsure").lower()

        if parsed_answer not in ["yes", "no", "unsure"]:
            parsed_answer = "unsure"

    except (json.JSONDecodeError, AttributeError):
        parsed_answer = "unsure"

    return {"parsed_answer": parsed_answer}


def node_store_answer(state: GraphState):
    """Stores the parsed answer and updates the list of questions to ask."""
    key = state['current_question_key']
    parsed_answer = state['parsed_answer']

    mapped_value = ANSWER_MAPPING[key][parsed_answer]
    state['collected_data'][key] = mapped_value

    remaining_keys = state['question_keys_to_ask'][1:]
    next_question_key = remaining_keys[0] if remaining_keys else None

    return {
        "collected_data": state['collected_data'],
        "question_keys_to_ask": remaining_keys,
        "current_question_key": next_question_key
    }


def node_handle_unsure(state: GraphState):
    """Handles an 'unsure' response by preparing to re-ask the question."""
    ai_message = "I see. Let's try that one again just to be sure."
    # We just update the history. The re-asking will happen in the 'ask_question' node.
    return {"conversation_history": state['conversation_history'] + [f"AI: {ai_message}"]}


def node_make_prediction(state: GraphState):
    """Prepares the final data and calls the SVM model pipeline."""
    from model_pipeline import preprocess_and_predict

    final_data = {**state['initial_user_data'], **state['collected_data']}

    if 'jundice' not in final_data:
        final_data['jundice'] = 'unsure'

    prediction, confidence = preprocess_and_predict(final_data)
    return {"final_prediction": prediction, "prediction_confidence": confidence}


# --- Conditional Edges ---

def edge_decide_after_parse(state: GraphState):
    """Decides whether to store the answer or re-ask the question."""
    if state['parsed_answer'] == 'unsure':
        return "re_ask"
    else:
        return "store_and_maybe_ask_next" # New path name

# --- Build the Graph ---

def create_graph():
    workflow = StateGraph(GraphState)

    # We now have two distinct graphs that we will call from main.py
    # Graph 1: Process a user's response
    workflow.add_node("parse_response", node_parse_response)
    workflow.add_node("store_answer", node_store_answer)
    workflow.add_node("handle_unsure", node_handle_unsure)

    workflow.add_conditional_edges(
        "parse_response",
        edge_decide_after_parse,
        {
            "re_ask": "handle_unsure",
            "store_and_maybe_ask_next": "store_answer"
        }
    )
    workflow.add_edge("handle_unsure", END)
    workflow.add_edge("store_answer", END)

    # Graph 2: Ask a question (and maybe predict)
    # This part is now mostly handled in main.py, but we keep the nodes.
    workflow.add_node("ask_question", node_ask_question)
    workflow.add_node("make_prediction", node_make_prediction)
    workflow.add_edge("ask_question", END)
    workflow.add_edge("make_prediction", END)

    workflow.set_entry_point("parse_response")

    return workflow.compile()