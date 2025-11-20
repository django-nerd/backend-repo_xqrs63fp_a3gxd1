"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
    image: Optional[str] = Field(None, description="Image URL")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    weight_g: Optional[int] = Field(None, ge=0, description="Weight in grams")

class OrderItem(BaseModel):
    product_id: str = Field(..., description="Associated product ID")
    title: str = Field(..., description="Product title at time of order")
    price: float = Field(..., ge=0, description="Unit price at time of order")
    quantity: int = Field(..., ge=1, description="Quantity of this item")

class Order(BaseModel):
    """
    Orders collection schema
    Collection name: "order"
    """
    customer_name: str = Field(...)
    email: str = Field(...)
    phone: str = Field(...)
    address_line: str = Field(...)
    city: str = Field(...)
    pincode: str = Field(...)
    payment_method: str = Field(..., description="cod | card")
    items: List[OrderItem] = Field(...)
    subtotal: float = Field(..., ge=0)
    shipping: float = Field(..., ge=0)
    total: float = Field(..., ge=0)
    status: str = Field("pending", description="Order status")
