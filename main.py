import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Shoe

app = FastAPI(title="Shoe Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Shoe Store API is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# --- Product endpoints ---

SAMPLE_SHOES: List[dict] = [
    {
        "name": "Air Zoom Runner",
        "brand": "Nike",
        "description": "Lightweight daily trainer with responsive ZoomX foam.",
        "price": 129.99,
        "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=60",
        "colors": ["Black", "Volt"],
        "sizes": [7, 8, 9, 10, 11, 12],
        "rating": 4.6,
        "category": "Running",
        "in_stock": True,
    },
    {
        "name": "Ultraboost 1.0",
        "brand": "Adidas",
        "description": "Iconic comfort with Boost midsole and Primeknit upper.",
        "price": 159.99,
        "image": "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=800&q=60",
        "colors": ["Core Black", "Cloud White"],
        "sizes": [6, 7, 8, 9, 10, 11],
        "rating": 4.7,
        "category": "Running",
        "in_stock": True,
    },
    {
        "name": "Classic Leather",
        "brand": "Reebok",
        "description": "Timeless street style with premium leather construction.",
        "price": 89.99,
        "image": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=800&q=60",
        "colors": ["White"],
        "sizes": [7, 8, 9, 10, 11, 12],
        "rating": 4.4,
        "category": "Lifestyle",
        "in_stock": True,
    },
    {
        "name": "Chuck 70 High",
        "brand": "Converse",
        "description": "Upgraded classic with durable canvas and cushioned insole.",
        "price": 74.99,
        "image": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=800&q=60",
        "colors": ["Black", "Parchment"],
        "sizes": [5, 6, 7, 8, 9, 10, 11],
        "rating": 4.5,
        "category": "Lifestyle",
        "in_stock": True,
    },
]


def _ensure_seed_data():
    # Check if collection has any documents; if none, insert samples
    try:
        existing = get_documents("shoe", {}, 1)
        if not existing:
            for item in SAMPLE_SHOES:
                try:
                    create_document("shoe", item)
                except Exception:
                    pass
    except Exception:
        # If database isn't available, just skip seeding
        pass


@app.get("/api/shoes")
def list_shoes(q: Optional[str] = None, brand: Optional[str] = None, limit: int = 50):
    _ensure_seed_data()
    filter_dict = {}
    if q:
        filter_dict["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"brand": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}},
        ]
    if brand:
        filter_dict["brand"] = {"$regex": brand, "$options": "i"}

    items = get_documents("shoe", filter_dict, limit)
    for it in items:
        _id = it.get("_id")
        if _id is not None:
            it["id"] = str(_id)
            del it["_id"]
    return {"items": items}


@app.post("/api/shoes")
def create_shoe(payload: Shoe):
    try:
        new_id = create_document("shoe", payload)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
