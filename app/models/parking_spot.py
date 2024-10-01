from sqlmodel import SQLModel, Field
from typing import Optional

class ParkingSpot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slot: int = Field(..., ge=1, le=20) 
    status: str  
