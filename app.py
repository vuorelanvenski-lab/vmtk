from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, RedirectResponse
from pydantic import BaseModel
import requests
import os
import base64
import time
from vercel.blob import put, list_objects, delete
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

canvas_store = {"image_bytes": None, "url": None, "last_fetch_time": 0}

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
            # 1. Find existing blobs to delete later
            old_urls = []
            try:
                res_list = list_objects(token=token)
                blobs = getattr(res_list, 'blobs', getattr(res_list, 'get', lambda x, y: [])('blobs', []))
                for b in blobs:
                    pathname = getattr(b, 'pathname', getattr(b, 'get', lambda x,y: '')('pathname', ''))
                    if "saved_canvas" in pathname:
                        old_urls.append(getattr(b, 'url', getattr(b, 'get', lambda x,y: '')('url', '')))
            except Exception as e:
                print(f"Error listing old blobs: {e}")

            # 2. Upload new blob with a completely unique URL
            res = put(
                "saved_canvas.png",
                image_bytes,
                access="public",
                add_random_suffix=True,
                token=token
            )
            url = getattr(res, 'url', None)
            if not url and hasattr(res, 'get'):
                url = res.get('url')
            canvas_store["url"] = url
            
            # 3. Delete old blobs so we don't waste storage space
            if url:
                for old_url in old_urls:
                    if old_url and old_url != url:
                        try:
                            delete(old_url, token=token)
                        except Exception:
                            pass
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
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if token:
        # Check for new blob URL at most once every 10 seconds
        if time.time() - canvas_store.get("last_fetch_time", 0) > 10:
            try:
                res = list_objects(token=token)
                blobs = getattr(res, 'blobs', getattr(res, 'get', lambda x, y: [])('blobs', []))
                
                blobs_list = list(blobs)
                blobs_list.sort(key=lambda x: str(getattr(x, 'uploaded_at', getattr(x, 'get', lambda k, v: '')('uploadedAt', ''))), reverse=True)
                
                found_url = None
                for b in blobs_list:
                    pathname = getattr(b, 'pathname', getattr(b, 'get', lambda x,y: '')('pathname', ''))
                    if "saved_canvas" in pathname:
                        found_url = getattr(b, 'url', getattr(b, 'get', lambda x,y: '')('url', ''))
                        break
                        
                if found_url:
                    canvas_store["url"] = found_url
                    canvas_store["last_fetch_time"] = time.time()
            except Exception as e:
                print(f"Vercel Blob list error: {e}")
                
        if canvas_store.get("url"):
            bust_url = f"{canvas_store['url']}?t={int(time.time())}"
            return RedirectResponse(url=bust_url)

    if canvas_store.get("image_bytes"):
        return Response(content=canvas_store["image_bytes"], media_type="image/png")
        
    raise HTTPException(status_code=404, detail="No canvas image saved")

@app.get("/api/debug_blob")
def debug_blob():
    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    if not token:
        return {"status": "error", "message": "BLOB_READ_WRITE_TOKEN is not set"}
    
    try:
        res = list_objects(token=token)
        blobs = getattr(res, 'blobs', getattr(res, 'get', lambda x, y: [])('blobs', []))
        
        blob_data = []
        for b in blobs:
            blob_data.append({
                "pathname": getattr(b, 'pathname', getattr(b, 'get', lambda x,y: '')('pathname', '')),
                "url": getattr(b, 'url', getattr(b, 'get', lambda x,y: '')('url', '')),
                "uploadedAt": str(getattr(b, 'uploaded_at', getattr(b, 'get', lambda x,y: '')('uploadedAt', '')))
            })
            
        return {
            "status": "success", 
            "token_starts_with": token[:10] + "..." if token else None,
            "blobs": blob_data,
            "canvas_store": {
                "url": canvas_store.get("url"),
                "has_bytes": "image_bytes" in canvas_store
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
