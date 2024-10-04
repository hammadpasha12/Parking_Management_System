from fastapi import APIRouter
from app.controllers.parking_controller import ParkingController,VehicleRegistrationController
from app.models.parking_spot import ParkingSpot,VehicleRegistration,VehicleRegistrationResponse
from typing import List,Dict,Any


router = APIRouter()

@router.get("/")
def hello():
    return {"message": "Parking System Management"}

@router.get("/slots/", response_model=List[ParkingSpot])
def read_parking_spots():
    return ParkingController.read_parking_spots()

@router.post("/slots/", response_model=ParkingSpot)
def create_parking_spot(parking_spot: ParkingSpot):
    return ParkingController.create_parking_spot(parking_spot)

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

@router.delete("/vehicle-registration/{slot_number}",response_model=Dict[str,Any])
def delete_vehicle_registration(slot_number: int):
    return VehicleRegistrationController.delete_vehicle_registration(slot_number)


@router.get("/vehicle-registration/{vehicle_id}/fee", response_model=dict)
def calculate_parking_fee(vehicle_id: int):
    return ParkingController.get_vehicle_fee(vehicle_id)

@router.get("/queue-status")
def get_queue_status():
    return {"queue_length": len(VehicleRegistrationController.waiting_queue)}


@router.get("/all-vehicle-records", response_model=List[dict])
def get_all_vehicle_records():
    return VehicleRegistrationController.get_all_vehicle_records()
