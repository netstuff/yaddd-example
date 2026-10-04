from pydantic import BaseModel


class PlaceOrderRequest(BaseModel):
    total: int


class OrderResponse(BaseModel):
    order_id: str
    total: int
