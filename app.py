from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, RedirectResponse
from pydantic import BaseModel
import requests
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

canvas_store = {"image_bytes": None, "url": None}

@app.post("/api/canvas")
def save_canvas(data: CanvasData):
    try:
        if "," in data.image_data:
            header, encoded = data.image_data.split(",", 1)
        else:
            encoded = data.image_data
            
        encoded = encoded.strip()
        padding = len(encoded) % 4
        if padding > 0:
            encoded += "=" * (4 - padding)
            
        image_bytes = base64.b64decode(encoded)
        
        token = os.environ.get("BLOB_READ_WRITE_TOKEN")
        if token:
            headers = {
                "authorization": f"Bearer {token}",
                "x-api-version": "7",
                "x-add-random-suffix": "0",
                "x-allow-overwrite": "1"
            }
            # Upload to Vercel Blob and overwrite the exact file
            res = requests.put(
                "https://blob.vercel-storage.com/saved_canvas.png",
                data=image_bytes,
                headers=headers
            )
            res.raise_for_status()
            res_data = res.json()
            canvas_store["url"] = res_data.get("url")
        else:
            canvas_store["image_bytes"] = image_bytes
            canvas_store["url"] = None
            
        return {"status": "success"}
    except requests.exceptions.RequestException as e:
        body = e.response.text if hasattr(e, 'response') and e.response is not None else str(e)
        print(f"Canvas save request error: {body}")
        raise HTTPException(status_code=500, detail=body)
    except Exception as e:
        print(f"Canvas save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/canvas_image")
def get_canvas_image():
    if canvas_store.get("url"):
        return RedirectResponse(url=canvas_store["url"])
        
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if token:
        try:
            headers = {
                "authorization": f"Bearer {token}",
                "x-api-version": "7"
            }
            res = requests.get("https://blob.vercel-storage.com", headers=headers)
            res.raise_for_status()
            blobs = res.json().get("blobs", [])
            
            # Sort by uploadedAt descending to get the latest
            blobs.sort(key=lambda x: x.get("uploadedAt", ""), reverse=True)
            for b in blobs:
                # Require exact match since we disable random suffix now
                if b.get("pathname") == "saved_canvas.png":
                    canvas_store["url"] = b.get("url")
                    return RedirectResponse(url=canvas_store["url"])
        except Exception as e:
            print(f"Vercel Blob list error: {e}")

    if canvas_store.get("image_bytes"):
        return Response(content=canvas_store["image_bytes"], media_type="image/png")
        
    raise HTTPException(status_code=404, detail="No canvas image saved")

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
