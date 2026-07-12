# Nutrigen 

Nutrigen is an intelligent, AI-powered meal planning application that uses the Gemini API and the USDA FoodData Central database to generate hyper-personalized, culturally authentic meal plans based on your precise macronutrient targets.

## Features

- **Intelligent RAG Pipeline**: Combines Google's Gemini LLM with FAISS vector search over USDA food data to ground AI generations in real nutritional science.
- **Cultural Authenticity**: Generates authentic dishes tailored strictly to the cuisine of your choice (e.g., South Indian, Mediterranean, American).
- **Macro Precision**: Takes in granular user data (Calories, Protein, Fat, Carbs, Sodium, etc.) to ensure the meals generated perfectly hit your targets without overwhelming you with raw math.
- **Advanced Controls**: Choose between 1-Day or 1-Week plans, dictate your Meals Per Day (from Intermittent Fasting to 4 Meals), and declare dietary preferences (Vegan, Pescatarian, etc.).
- **History Tracking**: Features a fully-fledged SQLite database with a Dashboard that automatically saves and retrieves your past generated meal plans.

## Tech Stack

- **Backend**: Python, FastAPI, SQLite
- **AI/ML**: Google Gemini (via REST API), SentenceTransformers, FAISS
- **External APIs**: USDA FoodData Central API
- **Frontend**: Vanilla HTML/CSS/JS (Zero-dependency, lightweight UI)

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Pranathigujjula/Nutrigen.git
cd Nutrigen
```

### 2. Set up the virtual environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory and add your API keys:
```env
GEMINI_API_KEY=your_gemini_key_here
USDA_API_KEY=your_usda_key_here
```
*(Note: You can get a USDA API key from [api.data.gov](https://api.data.gov/signup/) and a Gemini API key from Google AI Studio).*

### 5. Run the application
```bash
python main.py
```
Open your browser and navigate to `http://127.0.0.1:8000/`.

## Architecture 🏗️
- `main.py`: FastAPI server, routing, and schema definitions.
- `database.py`: SQLite initialization, user management, and history tracking.
- `rag_pipeline.py`: The core RAG logic (Retrieval-Augmented Generation) combining FAISS and Gemini.
- `usda_client.py`: The HTTP client for fetching live nutritional data from the USDA API.
- `static/`: Contains the frontend `index.html`, `index.css`, and `app.js`.
