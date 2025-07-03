# model_pipeline.py
import pandas as pd
import joblib
import json
from typing import Tuple

# Load all the necessary files once when the module is imported
try:
    # IMPORTANT: The SVM model must be saved with probability=True
    model = joblib.load('./saved_model/svm_model.joblib')
    scaler = joblib.load('./saved_model/scaler.joblib')
    with open('./saved_model/model_columns.json', 'r') as f:
        model_columns = json.load(f)
    with open('./saved_model/data_info.json', 'r') as f:
        data_info = json.load(f)
except FileNotFoundError:
    raise RuntimeError("Model files not found. Please run the training notebook to generate them, ensuring the model is saved with probability=True.")

def preprocess_and_predict(user_data: dict) -> Tuple[int, float]:
    """
    Takes the final dictionary of user data, preprocesses it,
    and returns the model's prediction and its confidence score.
    """
    # 1. Calculate 'result' score
    result_score = sum(v for k, v in user_data.items() if k.startswith('A'))
    user_data['result'] = result_score

    # Handle 'jaundice' if it was marked as unsure
    if user_data.get('jundice') == 'unsure':
        user_data['jundice'] = data_info['jaundice_mode']

    # 2. Create a DataFrame
    df = pd.DataFrame([user_data])

    # 3. Rename columns
    df = df.rename(columns={'country_of_residence': 'contry_of_res'})

    # 4. Process categorical features
    ethnicity_top = data_info['ethnicity_top_75']
    df['ethnicity_processed'] = df['ethnicity'].apply(
        lambda x: x if x in ethnicity_top else 'Others'
    )

    country_top = data_info['country_top_75']
    df['contry_of_res_processed'] = df['contry_of_res'].apply(
        lambda x: x if x in country_top else 'Others'
    )

    df = df.drop(['ethnicity', 'contry_of_res'], axis=1)

    # 5. One-Hot Encode
    df = pd.get_dummies(df, columns=['ethnicity_processed', 'contry_of_res_processed'])

    # 6. Align columns
    df_aligned = df.reindex(columns=model_columns, fill_value=0)

    # 7. Scale numerical features
    cols_to_scale = ['age', 'result']
    df_aligned[cols_to_scale] = scaler.transform(df_aligned[cols_to_scale])

    # 8. Make prediction and get probabilities
    prediction = model.predict(df_aligned)[0]
    probabilities = model.predict_proba(df_aligned)[0]
    
    # Get the confidence score for the predicted class
    confidence = probabilities[prediction]

    return int(prediction), float(confidence)