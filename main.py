import os
import io
import uuid
import requests
import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
from ultralytics import YOLO
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Load YOLOv8 Medium (Balance of speed and accuracy)
model = YOLO("yolov8m.pt")

CLIENT_ID = os.getenv("FATSECRET_CLIENT_ID")
CLIENT_SECRET = os.getenv("FATSECRET_CLIENT_SECRET")

# Validation List: Prevents the app from assigning carbs to non-edible objects
FOOD_ONLY_LIST = ["apple", "banana", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "sandwich", "bowl", "cup"]

auth_cache = {"token": None}

class BolusRequest(BaseModel):
    total_carbs: float
    current_bg: float
    target_bg: float
    carb_ratio: float
    sensitivity_factor: float

def get_token():
    if auth_cache["token"]: return auth_cache["token"]
    url = "https://oauth.fatsecret.com/connect/token"
    try:
        r = requests.post(url, auth=(CLIENT_ID, CLIENT_SECRET), data={"grant_type": "client_credentials", "scope": "basic"})
        token = r.json()["access_token"]
        auth_cache["token"] = token
        return token
    except: return None

def get_nutrition(label):
    if label not in FOOD_ONLY_LIST: return {"carbs": 0, "gi": 0, "is_food": False}
    
    # When YOLO detects 'bowl', FatSecret searches for the contents
    mapping = {"bowl": "noodle soup", "cup": "juice", "bottle": "soda"}
    query = mapping.get(label, label)
    
    token = get_token()
    if not token: return {"carbs": 20, "gi": 55, "is_food": True}
    
    try:
        s_url = "https://platform.fatsecret.com/rest/server.api"
        h = {"Authorization": f"Bearer {token}"}
        # Searches for food
        s_res = requests.get(s_url, headers=h, params={"method": "foods.search", "search_expression": query, "format": "json", "max_results": 1}).json()
        fid = s_res["foods"]["food"]["food_id"]
        # Gets detailed carbs
        d_res = requests.get(s_url, headers=h, params={"method": "food.get.v2", "food_id": fid, "format": "json"}).json()
        servs = d_res["food"]["servings"]["serving"]
        best = servs[0] if isinstance(servs, list) else servs
        carbs = float(best.get("carbohydrate", 0))
        
        # Hardcoded safety fallbacks for common detection errors
        if label == "pizza" and carbs < 10: carbs = 35.0
        if label == "bowl" and carbs < 10: carbs = 45.0
        
        return {"carbs": carbs, "gi": 60 if label in ["bowl", "pizza", "cake"] else 40, "is_food": True}
    except: return {"carbs": 15, "gi": 55, "is_food": True}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    img_data = await file.read()
    img = Image.open(io.BytesIO(img_data)).convert("RGB")
    res = model(img, conf=0.3)
    
    foods, total_carbs, total_gi, food_count = [], 0, 0, 0
    for r in res:
        for box in r.boxes:
            label = model.names[int(box.cls[0])]
            nutri = get_nutrition(label)
            
            # Portion sizing based on bounding box area
            area_ratio = ((box.xyxy[0][2]-box.xyxy[0][0]) * (box.xyxy[0][3]-box.xyxy[0][1])) / (img.width * img.height)
            portion = 0.8 if area_ratio < 0.05 else 1.2 if area_ratio < 0.15 else 2.2
            final_carbs = nutri["carbs"] * portion if nutri["is_food"] else 0
            
            foods.append({
                "name": label, 
                "carbs": round(final_carbs, 2), 
                "is_food": nutri["is_food"], 
                "confidence": round(float(box.conf[0]), 2)
            })
            
            if nutri["is_food"]:
                total_carbs += final_carbs
                total_gi += nutri["gi"]
                food_count += 1

    avg_gi = total_gi / food_count if food_count > 0 else 55
    gl = (total_carbs * avg_gi) / 100
    risk = "High" if gl > 20 else "Moderate" if gl > 10 else "Low"

    return {"id": str(uuid.uuid4())[:6].upper(), "foods": foods, "total_carbs": round(total_carbs, 2), "glycemic_load": round(gl, 2), "risk": risk}

@app.post("/calculate_bolus")
async def calculate_bolus(data: BolusRequest):
    food_insulin = data.total_carbs / data.carb_ratio
    correction = max(0, (data.current_bg - data.target_bg) / data.sensitivity_factor)
    return {
        "total_units": round(food_insulin + correction, 1),
        "food_units": round(food_insulin, 1),
        "correction_units": round(correction, 1)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)