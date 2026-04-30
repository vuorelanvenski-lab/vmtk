import requests
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RESTAURANT_ID = "c9266fa6-dd31-4800-92b2-1a41b6267613"
BASE_URL = "https://menu.leijonacatering.fi/AromieMenus/FI/Default/Leijona/HoikanhoviKajaani/api"

def get_current_week_dates():
    today = datetime.now()
    # Monday is 0, Sunday is 6
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Format: 2026-04-27T00:00:00.000Z
    start_str = start_of_week.strftime("%Y-%m-%dT00:00:00.000Z")
    end_str = end_of_week.strftime("%Y-%m-%dT00:00:00.000Z")
    
    return start_str, end_str

def fetch_diner_groups(start_date, end_date):
    url = f"{BASE_URL}/GetRestaurantPublicDinerGroups"
    params = {
        "id": RESTAURANT_ID,
        "startDate": start_date,
        "endDate": end_date
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_meals_for_group(diner_group, start_date, end_date):
    url = f"{BASE_URL}/Common/Restaurant/RestaurantMeals"
    params = {
        "Id": RESTAURANT_ID,
        "StartDate": start_date,
        "EndDate": end_date
    }
    headers = {
        "Content-Type": "application/json"
    }
    if diner_group.get("SuitabilityDietIds") is None:
        diner_group["SuitabilityDietIds"] = []
    
    response = requests.post(url, params=params, json=diner_group, headers=headers)
    response.raise_for_status()
    return response.json()

def parse_meals(raw_data):
    # raw_data is a list of days
    parsed_menu = []
    for day in raw_data:
        date_str = day.get("MenuDate") # e.g. "ma 27.4.2026"
        day_menu = {
            "date": date_str,
            "meals": []
        }
        for meal in day.get("Meals", []):
            meal_info = {
                "meal_name": meal.get("MealName"),
                "dishes": []
            }
            for dish in meal.get("Dishes", []):
                dish_info = {
                    "name": dish.get("DishName"),
                    "diets": dish.get("DietDetails", "")
                }
                meal_info["dishes"].append(dish_info)
            day_menu["meals"].append(meal_info)
        parsed_menu.append(day_menu)
    return parsed_menu

def fetch_foodlist():
    """
    Fetches the foodlist from the Leijona Catering API for Conscripts and Staff.
    """
    try:
        start_date, end_date = get_current_week_dates()
        logger.info(f"Fetching menu for week {start_date} to {end_date}")
        
        groups = fetch_diner_groups(start_date, end_date)
        
        conscript_group = None
        staff_group = None
        
        for g in groups:
            name = g.get("Name", "")
            if "Varusmiehet" in name and "varuskunta" in name:
                conscript_group = g
            elif "Henkilöstö" in name:
                staff_group = g
                
        if not conscript_group or not staff_group:
            logger.error("Could not find required diner groups")
            return {"error": "Diner groups not found"}
            
        conscript_meals_raw = fetch_meals_for_group(conscript_group, start_date, end_date)
        staff_meals_raw = fetch_meals_for_group(staff_group, start_date, end_date)
        
        result = {
            "week_start": start_date,
            "week_end": end_date,
            "conscript_menu": parse_meals(conscript_meals_raw),
            "staff_menu": parse_meals(staff_meals_raw)
        }
        
        logger.info("Successfully fetched and parsed menus")
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response body: {e.response.text}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import json
    print(json.dumps(fetch_foodlist(), indent=2))
