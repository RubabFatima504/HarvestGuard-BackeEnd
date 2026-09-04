"""Request/Response models"""
from pydantic import BaseModel
from typing import Optional


class BatchCreate(BaseModel):
    crop_id: str                          # "mango_sindhri"
    quantity_kg: float                    # 1000
    harvest_date: str                     # "2026-08-20"
    location_district: str                # "Mirpurkhas"
    location_province: str = "Sindh"
    latitude: float                       # 25.5276
    longitude: float                      # 69.0159
    storage_type: str = "open_air"        # open_air / covered_shed / cold_storage
    current_temp_celsius: Optional[float] = None
    transport_available: bool = True
    hours_to_nearest_market: float = 3.0
    target_market_id: Optional[str] = None
    farmer_name: Optional[str] = None
    cooperative_name: Optional[str] = None


class BatchResponse(BaseModel):
    batch_id: str
    status: str
    message: str


class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    cooperative_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    id: int
    name: str
    email: str
    cooperative_name: Optional[str] = None
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    cooperative_name: Optional[str] = None