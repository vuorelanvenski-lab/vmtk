from fastapi import FastAPI, HTTPException
from scraper import fetch_foodlist

app = FastAPI(title="Foodlist API", description="API to fetch scraped food lists.")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Foodlist API. Access /api/foodlist to get the data."}

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
