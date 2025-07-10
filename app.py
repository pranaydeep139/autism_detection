# app.py
import streamlit as st
import requests
import json

# --- Configuration ---
# URL of your running FastAPI backend
API_URL = "https://autism-detection-1-gxzu.onrender.com/turn"

# Define the options for the dropdowns. These should match the data your model was trained on.
# These values are derived from your notebook's analysis.
ETHNICITY_OPTIONS = [
    'White-European', 'Asian', 'Middle Eastern', 'Black', 'South Asian',
    'Hispanic', 'Latino', 'Pasifika', 'Turkish', 'Others'
]
GENDER_OPTIONS = ['Female', 'Male']

# A simplified list of countries from your dataset's top 75%
COUNTRY_OPTIONS = [
    'United States', 'United Kingdom', 'India', 'Australia', 'Canada',
    'New Zealand', 'United Arab Emirates', 'Jordan', 'Sri Lanka', 'Malaysia',
    'Netherlands', 'Ireland', 'Afghanistan', 'Others' # 'Others' for everything else
]


# --- Main App Logic ---
def main():
    st.set_page_config(page_title="Autism Screening Assistant", layout="centered")

    st.title("🤖 Autism Screening Assistant")
    st.markdown("""
    Welcome! This is an interactive tool to help screen for traits associated with Autism Spectrum Disorder (ASD).
    Please answer the questions as accurately as you can.

    **Disclaimer:** This is a screening tool, not a diagnostic tool. The results are not a medical diagnosis.
    Please consult a qualified healthcare professional for any health concerns.
    """)

    # Initialize session state variables to manage the conversation flow
    if 'screening_started' not in st.session_state:
        st.session_state.screening_started = False
    if 'langgraph_state' not in st.session_state:
        st.session_state.langgraph_state = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'is_finished' not in st.session_state:
        st.session_state.is_finished = False
    if 'prediction' not in st.session_state: # <<< NEW
        st.session_state.prediction = None
    if 'confidence' not in st.session_state: # <<< NEW
        st.session_state.confidence = None


    # --- Section 1: Initial Data Collection Form ---
    if not st.session_state.screening_started:
        with st.form("initial_data_form"):
            st.subheader("First, let's get some basic information:")

            age = st.number_input("Age", min_value=18, max_value=64, value=25, step=1)
            gender_str = st.selectbox("Gender", options=GENDER_OPTIONS)
            ethnicity = st.selectbox("Ethnicity", options=ETHNICITY_OPTIONS)
            country = st.selectbox("Country of Residence", options=COUNTRY_OPTIONS)

            submitted = st.form_submit_button("Start Screening")

            if submitted:
                # Map gender string to integer (0 for Female, 1 for Male)
                gender_int = 1 if gender_str == 'Male' else 0

                # Prepare the initial data payload for the first API call
                initial_data = {
                    "age": age,
                    "gender": gender_int,
                    "ethnicity": ethnicity,
                    "country_of_residence": country
                }

                # Make the first API call to start the conversation
                try:
                    with st.spinner("Initializing the conversation..."):
                        response = requests.post(
                            API_URL,
                            json={"initial_data": initial_data}
                        )
                        response.raise_for_status() # Raises an exception for 4XX/5XX errors

                    # Process the successful response
                    data = response.json()
                    st.session_state.langgraph_state = data['state']
                    st.session_state.messages.append({"role": "assistant", "content": data['ai_message']})
                    st.session_state.screening_started = True
                    st.rerun() # Rerun the script to move to the chat interface

                except requests.exceptions.RequestException as e:
                    st.error(f"Could not connect to the backend. Please ensure it's running. Error: {e}")

    # --- Section 2: Interactive Chat Interface ---
    else:
        # Display the chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # <<< NEW SECTION: Display final prediction slider if finished >>>
        if st.session_state.is_finished:
            st.markdown("---")
            st.subheader("Screening Result Indicator")

            if st.session_state.prediction is not None and st.session_state.confidence is not None:
                prediction = st.session_state.prediction
                confidence = st.session_state.confidence

                # Calculate the probability of the positive class (ASD traits present)
                # If prediction is 1 (Positive), prob_positive is the confidence.
                # If prediction is 0 (Negative), prob_positive is 1 - confidence.
                prob_positive = confidence if prediction == 1 else 1 - confidence
                slider_value = int(prob_positive * 100)

                # Use columns to create labels on either side of the slider
                col1, col2, col3 = st.columns([2, 6, 2])
                with col1:
                    st.markdown("<p style='text-align: right; font-weight: bold;'>Negative</p>", unsafe_allow_html=True)
                with col2:
                    # The slider is disabled and its label is hidden for a cleaner look
                    st.slider(
                        "Result",
                        min_value=0,
                        max_value=100,
                        value=slider_value,
                        disabled=True,
                        label_visibility="hidden"
                    )
                with col3:
                    st.markdown("<p style='font-weight: bold;'>Positive</p>", unsafe_allow_html=True)

        # Get user input, but only if the conversation is not finished
        if not st.session_state.is_finished:
            if prompt := st.chat_input("Your answer..."):
                # Add user message to chat history and display it
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Prepare the payload for the backend
                payload = {
                    "state": st.session_state.langgraph_state,
                    "user_response": prompt
                }

                # Call the backend to get the next step in the conversation
                try:
                    with st.spinner("AI is thinking..."):
                        response = requests.post(API_URL, json=payload)
                        response.raise_for_status()

                    data = response.json()

                    # Update state and display AI's response
                    st.session_state.langgraph_state = data['state']
                    st.session_state.is_finished = data['is_finished']
                    # <<< MODIFIED: Store prediction and confidence when finished >>>
                    if st.session_state.is_finished:
                        st.session_state.prediction = data.get('prediction')
                        st.session_state.confidence = data.get('confidence')


                    with st.chat_message("assistant"):
                        st.markdown(data['ai_message'])
                    st.session_state.messages.append({"role": "assistant", "content": data['ai_message']})

                    # Rerun to update the UI (this will also show the slider if finished)
                    st.rerun()

                except requests.exceptions.RequestException as e:
                    st.error(f"An error occurred. Please try again. Error: {e}")


if __name__ == "__main__":
    main()