import json
import logging
import requests
import numpy as np
import faiss
import os
from sentence_transformers import SentenceTransformer
from usda_client import USDAClient

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.usda_client = USDAClient()
        self.api_key = os.getenv("GEMINI_API_KEY")

        # Load a small, fast local embedding model
        logger.info("Loading sentence transformer model...")
        try:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = self.embedder.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to load sentence transformer: {e}")
            self.embedder = None
            
        # Initialize FAISS Index (L2 distance)
        if self.embedder:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.food_registry = [] # Maps index to food data
        
    def populate_knowledge_base(self, queries: list, api_key: str):
        """Fetch foods from USDA and build the FAISS index."""
        if not self.embedder:
            logger.warning("Embedder not loaded, skipping KB population.")
            return

        self.usda_client.api_key = api_key
        all_foods = []
        for q in queries:
            foods = self.usda_client.search_food(q, page_size=10)
            all_foods.extend(foods)
            
        if not all_foods:
            logger.warning("No foods retrieved from USDA.")
            return

        texts = []
        for food in all_foods:
            desc = food.get("description", "")
            cals = food.get("nutrients", {}).get("calories", "unknown")
            text = f"{desc} ({cals} kcal)"
            texts.append(text)
            self.food_registry.append(food)
            
        embeddings = self.embedder.encode(texts)
        self.index.add(np.array(embeddings).astype('float32'))
        logger.info(f"Added {len(texts)} items to vector database.")

    def retrieve(self, query: str, top_k: int = 5):
        if not self.embedder or self.index.ntotal == 0:
            return []
        
        query_emb = self.embedder.encode([query])
        distances, indices = self.index.search(np.array(query_emb).astype('float32'), top_k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.food_registry):
                results.append(self.food_registry[idx])
        return results

    def generate_meal_plan(self, user_row: dict, query: str) -> str:
        # Parse profile data
        try:
            profile = json.loads(user_row.get('profile_data', '{}'))
        except:
            profile = {}

        # 1. Retrieve relevant food items based on query/preferences
        search_query = f"{query} {profile.get('dietary_preferences', '')} {profile.get('available_foods', '')}"
        retrieved_foods = self.retrieve(search_query, top_k=10)
        
        context_str = "Available USDA Food Items (use these as reference):\n"
        for f in retrieved_foods:
            desc = f.get('description', '')
            nutrients = f.get('nutrients', {})
            cals = nutrients.get('calories', 'N/A')
            prot = nutrients.get('protein', 'N/A')
            fat = nutrients.get('fat', 'N/A')
            carbs = nutrients.get('carbs', 'N/A')
            context_str += f"- {desc}: {cals} kcal (P: {prot}g, F: {fat}g, C: {carbs}g)\n"

        if not retrieved_foods:
            context_str += "- No specific local USDA data retrieved. Use general knowledge.\n"

        # 2. Construct Prompt
        # Optional Drink Logic
        drink_rule = ""
        if "2 Meals" in profile.get('meals_per_day', ''):
            drink_rule = "5. You MUST include one customized, culturally appropriate Drink (e.g. Buttermilk, Green Tea, Protein Shake) for each day since they are only eating 2 meals."
            
        prompt = f"""You are an expert culinary nutritionist. 
Your job is to generate a highly personalized, delicious, and realistic {profile.get('plan_duration', '1 Day')} meal plan for the user.

CRITICAL CUISINE RULE: The meal plan MUST authentically match the requested cuisine ({profile.get('cuisine_type', 'N/A')}). 
For example, if the user requests South Indian, you MUST generate authentic dishes like Dosa, Idli, Sambar, or Chicken Chettinad. Do NOT generate weird combinations like "Beef and Broccoli" or "Salmon Salad" for a South Indian diet! If the provided USDA ingredients do not fit the cuisine, ignore them and invent culturally accurate dishes.

USER PROFILE (Do NOT print these exact macro numbers in the final output):
- Name: {user_row.get('name', 'User')}
- Cuisine: {profile.get('cuisine_type', 'N/A')}
- Target Calories: {profile.get('calories', 'N/A')} kcal
- Target Protein: {profile.get('protein', 'N/A')} g
- Target Carbs: {profile.get('carbs', 'N/A')} g
- Target Fat: {profile.get('fat', 'N/A')} g
- Target Fiber: {profile.get('fiber', 'N/A')} g
- Target Sodium: {profile.get('sodium', 'N/A')} mg
- Target Cholesterol: {profile.get('cholesterol', 'N/A')} mg
- Sugar Limit: {profile.get('sugar_limit', 'N/A')} g
- Diet/Preferences: {profile.get('dietary_preferences', 'N/A')}
- Restrictions: {profile.get('dietary_restrictions', 'N/A')}
- Meals per Day: {profile.get('meals_per_day', '3 Meals')}
- Plan Duration: {profile.get('plan_duration', '1 Day')}

AVAILABLE USDA INGREDIENTS (Use these ONLY if they authentically fit the requested cuisine):
{context_str}

FORMATTING RULES:
1. Do NOT show tables, charts, or raw macro/calorie numbers. The user does not want to see the math.
2. Do NOT list raw individual items (e.g. "Rice: 1 serving"). Instead, create a real dish ("Lemon Rice with Roasted Peanuts").
3. Format as a beautiful, structured menu spanning the requested duration ({profile.get('plan_duration', '1 Day')}).
4. For each day, strictly follow the requested Meals per Day ({profile.get('meals_per_day', '3 Meals')}).
{drink_rule}
5. For each meal, give the dish a catchy cultural name, followed by a short, appetizing description.
"""

        # 3. Call Gemini REST API directly with fallback models
        models_to_try = [
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-flash-lite-latest",
            "gemini-2.0-flash-lite-001",
            "gemini-3.5-flash"
        ]
        
        last_error = "Unknown Error"
        for model_name in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                
                response = requests.post(url, headers=headers, json=payload)
                response_data = response.json()
                
                if response.status_code == 200:
                    return response_data["candidates"][0]["content"]["parts"][0]["text"]
                
                error_msg = response_data.get("error", {}).get("message", "Unknown API Error")
                last_error = f"{model_name}: {error_msg}"
                logger.warning(f"Failed with {model_name}: {error_msg}")
                
            except Exception as e:
                last_error = f"{model_name}: {e}"
                logger.error(f"Exception with {model_name}: {e}")
                
        return f"Failed to generate meal plan using Gemini after trying multiple models. Your Google API key might have hit a hard rate limit or quota.\n\nFinal Error: {last_error}\n\nPlease wait about 1 minute and try again."

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    pipeline = RAGPipeline()
    print(pipeline.generate_meal_plan({"name": "Test User", "profile_data": '{"calories": 2000, "dietary_preferences": "Vegetarian", "intervention_duration": "1-day"}'}, "I want a high protein diet"))
