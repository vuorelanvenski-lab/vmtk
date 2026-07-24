from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, RedirectResponse
from pydantic import BaseModel
import requests
import os
import base64
import time
from scraper import fetch_foodlist

app = FastAPI(title="Foodlist API", description="API to fetch scraped food lists.")

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

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
