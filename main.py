# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from typing import List, Dict, Optional
import os
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

from graph import create_graph, QUESTIONS
from prompts import FINAL_RESPONSE_PROMPT

# Initialize the app and graph
app = FastAPI(
    title="Autism Screening Chatbot",
    description="An interactive chatbot to gather data for an ASD screening model.",
    version="1.0.0"
)

# Define the origins that are allowed to connect.
# We'll allow our deployed Streamlit app and localhost for testing.
origins = [
    "https://*.streamlit.app", # Allows any deployed Streamlit app
    "http://localhost",
    "http://localhost:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

graph_app = create_graph()
nodes = graph_app.nodes

# Configure Gemini API for final response
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
final_response_model = genai.GenerativeModel('gemini-1.5-flash')

# --- Pydantic Models for the API ---
class InitialData(BaseModel):
    age: int = Field(..., description="User's age.")
    gender: int = Field(..., description="User's gender (0 for f, 1 for m).")
    ethnicity: str = Field(..., description="User's ethnicity.")
    country_of_residence: str = Field(..., description="User's country of residence.")

class StateForAPI(BaseModel):
    initial_user_data: Dict = {}
    collected_data: Dict = {}
    question_keys_to_ask: List[str] = Field(default_factory=list)
    current_question_key: str = ""
    conversation_history: List[str] = Field(default_factory=list)

class ApiRequest(BaseModel):
    state: Optional[StateForAPI] = None
    user_response: str = ""
    initial_data: Optional[InitialData] = None

class ApiResponse(BaseModel):
    state: StateForAPI
    ai_message: str
    is_finished: bool
    prediction: Optional[int] = None
    confidence: Optional[float] = None

# --- Main API Endpoint ---
@app.post("/turn", response_model=ApiResponse)
def take_turn(request: ApiRequest):
    """
    Handles a single turn by directly invoking the necessary nodes one by one
    and explicitly merging the state after each step.
    """
    if request.state is None: # First turn: Just ask the first question
        if not request.initial_data:
            raise HTTPException(status_code=400, detail="Initial data is required.")

        all_keys = list(QUESTIONS.keys())
        current_state = {
            "initial_user_data": request.initial_data.dict(),
            "collected_data": {},
            "question_keys_to_ask": all_keys,
            "current_question_key": all_keys[0],
            "conversation_history": [],
        }
        ask_result = nodes["ask_question"].invoke(current_state)
        current_state.update(ask_result)

    else: # Subsequent turns
        current_state = request.state.dict()
        current_state["user_response"] = request.user_response
        current_state["conversation_history"] += [f"User: {request.user_response}"]

        parse_result = nodes["parse_response"].invoke(current_state)
        current_state.update(parse_result)

        if current_state["parsed_answer"] == "unsure":
            handle_unsure_result = nodes["handle_unsure"].invoke(current_state)
            current_state.update(handle_unsure_result)
            ask_result = nodes["ask_question"].invoke(current_state)
            current_state.update(ask_result)
        else:
            store_result = nodes["store_answer"].invoke(current_state)
            current_state.update(store_result)

            if not current_state.get("question_keys_to_ask"):
                prediction_result = nodes["make_prediction"].invoke(current_state)
                current_state.update(prediction_result)

                # Generate the final empathetic response
                prediction_text = _format_final_response(
                    current_state['final_prediction'],
                    current_state['prediction_confidence'],
                    current_state['conversation_history']
                )
                current_state['conversation_history'] += [f"AI: {prediction_text}"]

                if current_state.get("current_question_key") is None:
                    current_state["current_question_key"] = ""

                ai_message = current_state['conversation_history'][-1].replace("AI: ", "")
                response_state = StateForAPI(**{k: v for k, v in current_state.items() if k in StateForAPI.model_fields})
                return ApiResponse(
                    state=response_state,
                    ai_message=ai_message,
                    is_finished=True,
                    prediction=current_state.get('final_prediction'),
                    confidence=current_state.get('prediction_confidence')
                )
            else:
                ask_result = nodes["ask_question"].invoke(current_state)
                current_state.update(ask_result)

    if current_state.get("current_question_key") is None:
        current_state["current_question_key"] = ""

    ai_message = current_state['conversation_history'][-1].replace("AI: ", "") if current_state['conversation_history'] else ""
    response_state = StateForAPI(**{k: v for k, v in current_state.items() if k in StateForAPI.model_fields})

    return ApiResponse(state=response_state, ai_message=ai_message, is_finished=False, prediction=None)


def _format_final_response(prediction: int, confidence: float, conversation_history: list) -> str:
    """Generates the final response using Gemini."""
    
    # Format the conversation history for the prompt
    history_str = "\n".join(conversation_history)

    prompt = FINAL_RESPONSE_PROMPT.format(
        prediction= "some traits associated with ASD may be present" if prediction == 1 else "fewer traits associated with ASD were indicated",
        confidence_score=f"{confidence:.2%}",
        conversation_history=history_str
    )
    
    response = final_response_model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)