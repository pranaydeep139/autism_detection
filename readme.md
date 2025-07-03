# Autism Screening Assistant 🤖

An interactive web application that provides an autism spectrum disorder (ASD) screening tool using machine learning. The application features a conversational interface that guides users through evidence-based screening questions and provides personalized results.

## ⚠️ Important Disclaimer

**This is a screening tool, not a diagnostic tool.** The results are not a medical diagnosis. Please consult a qualified healthcare professional for any health concerns or for a formal evaluation.

## 🌟 Features

- **Interactive Conversational Interface**: Natural language processing for user-friendly interactions
- **Evidence-Based Screening**: Uses validated ASD screening questions
- **Machine Learning Predictions**: SVM model with confidence scoring
- **Personalized Results**: Tailored responses based on user interactions
- **Multi-Cultural Support**: Supports various ethnicities and countries
- **Real-time Processing**: Instant feedback and results

## 🏗️ Architecture

The application consists of several key components:

- **Frontend**: Streamlit web interface (`app.py`)
- **Backend API**: FastAPI server (`main.py`)
- **Conversation Management**: LangGraph state management (`graph.py`)
- **ML Pipeline**: SVM model with preprocessing (`model_pipeline.py`)
- **AI Integration**: Google Gemini for natural language processing
- **Configuration**: Prompts and question templates (`prompts.py`)

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **ML Framework**: scikit-learn (SVM)
- **AI/NLP**: Google Gemini API
- **State Management**: LangGraph
- **Data Processing**: pandas, joblib
- **API Client**: requests

## 📋 Prerequisites

- Python 3.8+
- Google Gemini API key
- Required Python packages (see installation section)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd autism-screening-assistant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_google_gemini_api_key_here
   ```

5. **Prepare the ML model**
   Ensure the following files exist in the `./saved_model/` directory:
   - `svm_model.joblib` (SVM model saved with `probability=True`)
   - `scaler.joblib` (Feature scaler)
   - `model_columns.json` (Model feature columns)
   - `data_info.json` (Data preprocessing information)

## 📁 Project Structure

```
autism-screening-assistant/
├── app.py                 # Streamlit frontend application
├── main.py                # FastAPI backend server
├── graph.py               # LangGraph conversation management
├── model_pipeline.py      # ML model pipeline
├── prompts.py             # AI prompts and question templates
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── saved_model/           # ML model files
│   ├── svm_model.joblib
│   ├── scaler.joblib
│   ├── model_columns.json
│   └── data_info.json
└── README.md
```

## 🔧 Usage

### Starting the Application

1. **Start the FastAPI backend**
   ```bash
   python main.py
   ```
   The API will be available at `http://127.0.0.1:8000`

2. **Start the Streamlit frontend**
   ```bash
   streamlit run app.py
   ```
   The web interface will be available at `http://localhost:8501`

### Using the Application

1. **Initial Setup**: Provide basic demographic information (age, gender, ethnicity, country)
2. **Screening Questions**: Answer the series of screening questions through the conversational interface
3. **Results**: Review your personalized screening results and recommendations

## 📊 Screening Questions

The application uses a validated set of screening questions covering:

- Sensory processing (A1)
- Attention to detail vs. big picture thinking (A2)
- Multitasking abilities (A3, A4)
- Social communication skills (A5, A6, A9)
- Theory of mind (A7, A10)
- Restricted interests (A8)
- Medical history (jaundice)
- Family history (autism)

## 🤖 AI Components

### Natural Language Processing
- **Google Gemini 2.5 Flash Lite**: Question presentation and response parsing
- **Google Gemini 1.5 Flash**: Final result generation

### Machine Learning
- **SVM Model**: Binary classification for ASD trait prediction
- **Feature Engineering**: Demographic and response preprocessing
- **Confidence Scoring**: Probability-based confidence metrics

## 🔒 Privacy and Data Handling

- No persistent data storage
- Session-based state management
- Secure API communication
- GDPR-compliant data handling practices

## 📈 Model Performance

The SVM model includes:
- **Preprocessing**: Feature scaling and categorical encoding
- **Training**: Balanced dataset with cross-validation
- **Evaluation**: Confidence scoring for predictions
- **Validation**: Evidence-based screening methodology

## 🔧 Configuration

### Supported Demographics

**Ethnicities**: White-European, Asian, Middle Eastern, Black, South Asian, Hispanic, Latino, Pasifika, Turkish, Others

**Countries**: United States, United Kingdom, India, Australia, Canada, New Zealand, United Arab Emirates, Jordan, Sri Lanka, Malaysia, Netherlands, Ireland, Afghanistan, Others

**Age Range**: 18-64 years

**Genders**: Male, Female

## 🚨 Error Handling

The application includes comprehensive error handling for:
- API connection failures
- Model prediction errors
- Invalid user inputs
- Network connectivity issues

## 📝 API Documentation

### Endpoints

#### `POST /turn`
Handles conversation turns and screening logic.

**Request Body:**
```json
{
  "state": {
    "initial_user_data": {},
    "collected_data": {},
    "question_keys_to_ask": [],
    "current_question_key": "",
    "conversation_history": []
  },
  "user_response": "string",
  "initial_data": {
    "age": 25,
    "gender": 1,
    "ethnicity": "White-European",
    "country_of_residence": "United States"
  }
}
```

**Response:**
```json
{
  "state": {...},
  "ai_message": "string",
  "is_finished": false,
  "prediction": 0,
  "confidence": 0.85
}
```

## 🧪 Testing

Run the application locally to test:
1. Start both backend and frontend servers
2. Navigate through the complete screening process
3. Verify API responses and model predictions
4. Test edge cases and error scenarios

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Based on established autism screening methodologies
- Powered by Google Gemini AI
- Built with modern web technologies
- Designed with accessibility in mind

## 📞 Support

For questions, issues, or contributions:
- Create an issue in the repository
- Contact the development team
- Review the documentation

---

**Remember**: This tool is designed to support, not replace, professional medical evaluation. Always consult with qualified healthcare professionals for medical concerns.