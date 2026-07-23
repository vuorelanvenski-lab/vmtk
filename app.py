from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import base64
from scraper import fetch_foodlist

app = FastAPI(title="Foodlist API", description="API to fetch scraped food lists.")

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

class CanvasData(BaseModel):
    image_data: str

@app.get("/canvas")
def get_canvas_page():
    return FileResponse("static/canvas.html")

@app.post("/api/canvas")
def save_canvas(data: CanvasData):
    try:
        # data.image_data looks like "data:image/png;base64,iVBORw0KGgo..."
        if "," in data.image_data:
            header, encoded = data.image_data.split(",", 1)
        else:
            encoded = data.image_data
            
        encoded = encoded.strip()
        padding = len(encoded) % 4
        if padding > 0:
            encoded += "=" * (4 - padding)
            
        image_bytes = base64.b64decode(encoded)
        with open("static/saved_canvas.png", "wb") as f:
            f.write(image_bytes)
        return {"status": "success"}
    except Exception as e:
        print(f"Canvas save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/foodlist")
def get_foodlist():
    """
    Endpoint to trigger the scraper and return the foodlist.
    """
    data = fetch_foodlist()
    
    if isinstance(data, dict) and "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
        
    return {"data": data}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
