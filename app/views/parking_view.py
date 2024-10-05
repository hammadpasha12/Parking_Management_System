from fastapi import APIRouter,Depends
from app.controllers.parking_controller import ParkingController,VehicleRegistrationController
from app.models.parking_spot import ParkingSpot,VehicleRegistration,VehicleRegistrationResponse
from typing import List,Dict,Any
from sqlmodel import Session
from app.database import get_db



router = APIRouter()

@router.get("/")
def hello():
    return {"message": "Parking System Management"}

@router.get("/slots/", response_model=List[ParkingSpot])
def read_parking_spots(db:Session = Depends(get_db)):
    return ParkingController.read_parking_spots(db)

@router.post("/slots/", response_model=ParkingSpot)
def create_parking_spot(parking_spot: ParkingSpot,db:Session = Depends(get_db)):
    return ParkingController.create_parking_spot(parking_spot,db)

@router.delete("/slots/{slot_id}", response_model=dict)
def delete_parking_spot(slot_id: int, db: Session = Depends(get_db)):
    return ParkingController.delete_parking_spot(slot_id,db)



# VEHICLE REGISTRATION

@router.post("/vehicle-registration", response_model=VehicleRegistration)
def create_vehicle_registration(vehicle_registration: VehicleRegistration,db:Session = Depends(get_db)):
    return VehicleRegistrationController.create_vehicle_registration(vehicle_registration,db)

@router.get("/vehicle-registration", response_model=List[VehicleRegistrationResponse])
def get_vehicle_registrations(db:Session = Depends(get_db)):
    return VehicleRegistrationController.read_vehicle_registrations(db)

@router.delete("/vehicle-registration/{slot_number}",response_model=Dict[str,Any])
def delete_vehicle_registration(slot_number: int, db: Session = Depends(get_db), rate_per_hour: int = 50):
    return VehicleRegistrationController.delete_vehicle_registration(slot_number,rate_per_hour,db)

@router.get("/vehicle-registration/{vehicle_id}/fee", response_model=dict,)
def calculate_parking_fee(vehicle_id: int, rate_per_hour: int = 50,db:Session = Depends(get_db)):
    return ParkingController.get_vehicle_fee(vehicle_id,rate_per_hour,db)

@router.get("/queue-status")
def get_queue_status():
    return {"queue_length": len(VehicleRegistrationController.waiting_queue)}


@router.get("/all-vehicle-records", response_model=List[dict])
def get_all_vehicle_records(db:Session = Depends(get_db)):
    return VehicleRegistrationController.get_all_vehicle_records(db)
