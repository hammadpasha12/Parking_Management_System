from fastapi import APIRouter
from app.controllers.parking_controller import ParkingController
from app.models.parking_spot import ParkingSpot
from typing import List

router = APIRouter()

@router.get("/")
def hello():
    return {"message": "Parking System Management"}

@router.post("/slots/", response_model=ParkingSpot)
def create_parking_spot(parking_spot: ParkingSpot):
    return ParkingController.create_parking_spot(parking_spot)

@router.get("/slots/", response_model=List[ParkingSpot])
def read_parking_spots():
    return ParkingController.read_parking_spots()

@router.delete("/slots/{slot_id}", response_model=dict)
def delete_parking_spot(slot_id: int):
    return ParkingController.delete_parking_spot(slot_id)
