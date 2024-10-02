from fastapi import APIRouter,HTTPException
from app.controllers.parking_controller import ParkingController,VehicleRegistrationController
from app.models.parking_spot import ParkingSpot,VehicleRegistration,VehicleRegistrationResponse
from typing import List
from sqlmodel import Session, select
from app.database import engine


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



# VEHICLE REGISTRATION

@router.post("/vehicle-registration", response_model=VehicleRegistration)
def create_vehicle_registration(vehicle_registration: VehicleRegistration):
    return VehicleRegistrationController.create_vehicle_registration(vehicle_registration)

@router.get("/vehicle-registration", response_model=List[VehicleRegistrationResponse])
def get_vehicle_registrations():
    return VehicleRegistrationController.read_vehicle_registrations()

@router.delete("/vehicle-registration/{vehicle_id}")
def delete_vehicle_registration(vehicle_id: int):
    return VehicleRegistrationController.delete_vehicle_registration(vehicle_id)


@router.get("/vehicle-registration/{vehicle_id}/calculate-fee", response_model=dict)
def calculate_parking_fee(vehicle_id: int):
    return ParkingController.get_vehicle_fee(vehicle_id)