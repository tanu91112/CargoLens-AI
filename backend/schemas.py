
from pydantic import BaseModel, ConfigDict


class UserRegister(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


from pydantic import BaseModel
from datetime import datetime


class ShipmentCreate(BaseModel):
    shipment_number: str
    supplier_name: str
    origin_country: str


class ShipmentResponse(BaseModel):
    id: int
    shipment_number: str
    supplier_name: str
    origin_country: str
    status: str
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    shipment_id: int
    document_type: str
    original_filename: str
    processing_status: str
    uploaded_by: int
    uploaded_at: datetime

    class Config:
        from_attributes = True