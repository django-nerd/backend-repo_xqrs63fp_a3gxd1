import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order, OrderItem

app = FastAPI(title="Jaggery Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Jaggery Store Backend"}

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
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Seed a single product (1kg and 500g jaggery powder variants)
@app.post("/seed")
def seed_products():
    try:
        existing = list(db["product"].find({"sku": {"$in": ["JAG-500", "JAG-1000"]}})) if db else []
        if existing:
            return {"inserted": 0, "message": "Products already exist"}
        p1 = Product(
            title="Jaggery Powder 500g",
            description="Pure, chemical-free jaggery powder. Perfect for tea, coffee and cooking.",
            price=2.49,
            category="jaggery",
            in_stock=True,
            image="/jaggery-500.jpg",
            sku="JAG-500",
            weight_g=500
        )
        p2 = Product(
            title="Jaggery Powder 1kg",
            description="Pure, chemical-free jaggery powder family pack.",
            price=4.49,
            category="jaggery",
            in_stock=True,
            image="/jaggery-1000.jpg",
            sku="JAG-1000",
            weight_g=1000
        )
        create_document("product", p1)
        create_document("product", p2)
        return {"inserted": 2}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products")
def list_products():
    try:
        items = get_documents("product")
        for it in items:
            it["_id"] = str(it["_id"]) if "_id" in it else None
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CartItem(BaseModel):
    product_id: str
    quantity: int

class CheckoutRequest(BaseModel):
    name: str
    email: str
    phone: str
    address_line: str
    city: str
    pincode: str
    payment_method: str  # cod | card (mock)
    cart: List[CartItem]

@app.post("/checkout")
def checkout(payload: CheckoutRequest):
    try:
        # fetch products
        ids = [ObjectId(ci.product_id) for ci in payload.cart]
        products = list(db["product"].find({"_id": {"$in": ids}}))
        product_map = {str(p["_id"]): p for p in products}

        items: List[OrderItem] = []
        subtotal = 0.0
        for ci in payload.cart:
            prod = product_map.get(ci.product_id)
            if not prod:
                raise HTTPException(status_code=404, detail=f"Product {ci.product_id} not found")
            line_total = float(prod.get("price", 0)) * ci.quantity
            subtotal += line_total
            items.append(OrderItem(
                product_id=ci.product_id,
                title=prod.get("title"),
                price=float(prod.get("price", 0)),
                quantity=ci.quantity
            ))
        shipping = 0.0 if subtotal >= 10 else 1.0
        total = subtotal + shipping

        order = Order(
            customer_name=payload.name,
            email=payload.email,
            phone=payload.phone,
            address_line=payload.address_line,
            city=payload.city,
            pincode=payload.pincode,
            payment_method=payload.payment_method,
            items=items,
            subtotal=round(subtotal, 2),
            shipping=round(shipping, 2),
            total=round(total, 2),
            status="paid" if payload.payment_method == "card" else "pending"
        )
        order_id = create_document("order", order)

        # Mock payment intent for "card" method
        payment_info = None
        if payload.payment_method == "card":
            payment_info = {"provider": "mock", "status": "succeeded", "transaction_id": order_id}

        return {"order_id": order_id, "total": order.total, "status": order.status, "payment": payment_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
