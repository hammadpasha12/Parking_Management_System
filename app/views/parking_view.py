from fastapi import APIRouter,Depends
from app.controllers.parking_controller import ParkingController,VehicleRegistrationController
from app.models.parking_spot import ParkingSpot,VehicleRegistration,VehicleRegistrationResponse,GenericResponse
from typing import List,Dict,Any
from sqlmodel import Session
from app.database import get_db



router = APIRouter()

@router.get("/")
def hello():
    return {"message": "Parking System Management"}

@router.get("/parking/", response_model=List[ParkingSpot])
def read_parking_spots(db:Session = Depends(get_db)):
    return ParkingController.read_parking_spots(db)

@router.post("/parking/", response_model=ParkingSpot)
def create_parking_spot(parking_spot: ParkingSpot,db:Session = Depends(get_db)):
    return ParkingController.create_parking_spot(parking_spot,db)

@router.delete("/parking/{slot_id}", response_model=GenericResponse)
def delete_parking_spot(slot_id: int, db: Session = Depends(get_db)):
    result = ParkingController.delete_parking_spot(slot_id,db)
    return GenericResponse(message=result.get("message"),data=result.get("next_vehicle"))



# VEHICLE REGISTRATION

@router.post("/vehicle-registration", response_model=VehicleRegistration)
def create_vehicle_registration(vehicle_registration: VehicleRegistration,db:Session = Depends(get_db)):
    return VehicleRegistrationController.create_vehicle_registration(vehicle_registration,db)

@router.get("/vehicle-registration", response_model=List[VehicleRegistrationResponse])
def get_vehicle_registrations(db:Session = Depends(get_db)):
    return VehicleRegistrationController.read_vehicle_registrations(db)

@router.delete("/vehicle-registration/{slot_number}",response_model=GenericResponse)
def delete_vehicle_registration(slot_number: int, db: Session = Depends(get_db), rate_per_hour: int = 50):
    result = VehicleRegistrationController.delete_vehicle_registration(slot_number,db,rate_per_hour) 
    return GenericResponse(message=result.get("message"),data=result.get("vehicle_details"))

@router.get("/vehicle-registration/{vehicle_id}/fee", response_model=GenericResponse)
def calculate_parking_fee(vehicle_id: int, rate_per_hour: int = 50,db:Session = Depends(get_db)):
    result=ParkingController.get_vehicle_fee(vehicle_id,rate_per_hour,db)
    return GenericResponse(message=f"The fee of {vehicle_id} is ",data=result)

@router.get("/queue-status",response_model=GenericResponse)
def get_queue_status():
    queue_length = len(VehicleRegistrationController.waiting_queue)
    return GenericResponse(message="The total car in the queue is",data=queue_length)


@router.get("/all-vehicle-records", response_model=GenericResponse)
def get_all_vehicle_records(db:Session = Depends(get_db)):
    records = VehicleRegistrationController.get_all_vehicle_records(db)
    return GenericResponse(message="The total vehicle record is",data=records)
