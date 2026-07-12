import requests
import json
import logging
import os

logger = logging.getLogger(__name__)

class USDAClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("USDA_API_KEY", "XBcdxuqgjv8DHoI6zkJrYAFTbmZFcBuhcvwnABcI")
        self.base_url = "https://api.nal.usda.gov/fdc/v1"

    def search_food(self, query: str, page_size: int = 5):
        """
        Search for food items in the USDA FoodData Central database.
        """
        url = f"{self.base_url}/foods/search"
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            foods = []
            for item in data.get("foods", []):
                food_info = {
                    "fdcId": item.get("fdcId"),
                    "description": item.get("description"),
                    "brandOwner": item.get("brandOwner", ""),
                    "nutrients": {}
                }
                
                # Extract key nutrients (Calories, Protein, Fat, Carbs)
                for nutrient in item.get("foodNutrients", []):
                    name = nutrient.get("nutrientName", "").lower()
                    if "energy" in name and "kcal" in nutrient.get("unitName", "").lower():
                        food_info["nutrients"]["calories"] = nutrient.get("value")
                    elif "protein" in name:
                        food_info["nutrients"]["protein"] = nutrient.get("value")
                    elif "lipid" in name or "fat" in name:
                        if "total" in name:
                            food_info["nutrients"]["fat"] = nutrient.get("value")
                    elif "carbohydrate" in name:
                        food_info["nutrients"]["carbs"] = nutrient.get("value")
                
                foods.append(food_info)
            return foods
            
        except requests.RequestException as e:
            logger.error(f"Error fetching data from USDA API: {e}")
            return []

if __name__ == "__main__":
    # Test the client
    client = USDAClient()
    results = client.search_food("apple")
    print(json.dumps(results, indent=2))
