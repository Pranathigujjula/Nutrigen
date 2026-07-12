from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import logging

# Load environment variables from .env file
load_dotenv()

from rag_pipeline import RAGPipeline
import database as db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically initialize USDA vector database in the background on startup
    logger = logging.getLogger(__name__)
    logger.info("Initializing USDA Vector DB in background...")
    try:
        rag.populate_knowledge_base(
            ["apple", "chicken breast", "rice", "broccoli", "salmon", "spinach", "oats"],
            os.getenv("USDA_API_KEY")
        )
    except Exception as e:
        logger.error(f"Failed to auto-populate USDA data: {e}")
    yield

app = FastAPI(title="Nutrigen", lifespan=lifespan)

# Mount static files for the frontend
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize RAG Pipeline for Gemini
rag = RAGPipeline()

class UserProfile(BaseModel):
    name: str
    password: str
    cuisine_type: str
    meals_per_day: str
    plan_duration: str
    calories: int
    protein: int
    fat: int
    carbs: int
    fiber: int
    sugar_limit: int
    sodium: int
    cholesterol: int
    food_history: str
    dietary_preferences: str
    dietary_restrictions: str
    available_foods: str
    meal_type: str
    portion_size: str
    intervention_duration: str
    food_intake_patterns: str
    nutritional_targets: str
    output_format: str

class MealPlanRequest(BaseModel):
    user_id: int
    query: str

class LoginRequest(BaseModel):
    name: str
    password: str

class SetupUSDA(BaseModel):
    api_key: str
    queries: list[str]

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Serve the main HTML file
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<html><body><h1>UI not built yet</h1><p>Please place index.html in the static/ folder.</p></body></html>"

@app.post("/api/users")
async def create_user(profile: UserProfile):
    profile_data = profile.model_dump(exclude={'name'})
    user_id = db.create_user(profile.name, profile_data)
    if not user_id:
        raise HTTPException(status_code=400, detail="Error creating user.")
    return {"message": "User created successfully", "user_id": user_id}

@app.put("/api/users/{user_id}")
async def update_user(user_id: int, profile: UserProfile):
    profile_data = profile.model_dump(exclude={'name'})
    db.update_user_profile(user_id, profile_data)
    return {"message": "User updated successfully"}


@app.post("/api/login")
async def login(req: LoginRequest):
    user = db.login_user(req.name, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {"message": "Login successful", "user_id": user['id'], "name": user['name']}

@app.post("/api/generate")
async def generate_plan(request: MealPlanRequest):
    user = db.get_user(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Generate Meal Plan using RAG and Gemini API
    plan = rag.generate_meal_plan(user, request.query)
    
    # Save to history
    db.save_meal_plan(request.user_id, plan)
    
    return {
        "status": "success",
        "meal_plan": plan
    }

@app.get("/api/history/{user_id}")
async def get_history(user_id: int):
    history = db.get_user_history(user_id)
    return {"status": "success", "history": history}

if __name__ == "__main__":
    import uvicorn
    # Run server locally (fixed IP from 120.0.0.1 to 127.0.0.1)
    uvicorn.run(app, host="127.0.0.1", port=8000)
