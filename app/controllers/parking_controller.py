import math
from datetime import datetime, timezone
from sqlmodel import Session, select
from fastapi import HTTPException,Depends
from app.models.parking_spot import ParkingSpot,VehicleRegistration
from app.database import get_db
from collections import deque
from sqlalchemy import text
from zoneinfo import ZoneInfo

PST = ZoneInfo('Asia/Karachi')

class ParkingController:
    @staticmethod
    def create_parking_spot(parking_spot: ParkingSpot,db:Session):
        try:
            if parking_spot.slot > 20:
                raise HTTPException(status_code=400, detail="Slot number cannot exceed 20.")
            
            existing_spot = db.exec(select(ParkingSpot).where(ParkingSpot.slot == parking_spot.slot)).first()
            if existing_spot:
                raise HTTPException(status_code=400,detail="Slot is already filled.")
            
            new_spot = ParkingSpot(slot=parking_spot.slot, status="available")
            db.add(new_spot)
            db.commit()
            db.refresh(new_spot)
            return new_spot
        
        # THIS EXCEPT BLOCK RERAISED HTTPException LIKE (Slot is already filled.) 
        except HTTPException as http_exc:
            raise http_exc
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured in creating parking spot:{e}")

    @staticmethod
    def read_parking_spots(db:Session):
        try:
            parking_spots = db.exec(select(ParkingSpot)).all()
            return parking_spots
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured in read_parking_spots:{e} ")
    
    @staticmethod
    def delete_parking_spot(slot_id: int,db:Session):
        try:
            spot_del = db.exec(select(ParkingSpot).where(ParkingSpot.id == slot_id)).first()
            if not spot_del:
                raise HTTPException(status_code=404, detail="Slot not found.")
            
            db.delete(spot_del)
            spot_del.status = "available"
            db.commit()

            remaining_spots = db.exec(select(ParkingSpot)).all()

            if not remaining_spots:
                reset_sequence_query= text("ALTER SEQUENCE parkingspot_id_seq RESTART WITH 1")
                db.exec(reset_sequence_query)
                db.commit()

            next_vehicle = VehicleRegistrationController.process_waiting_queue()

            if next_vehicle:
                return{"message":f"Slot {slot_id} is now available and assigned to the next vehicle in the queue."}
            
            return {"message": f"Parking spot {slot_id} has been deleted"}
        
        except HTTPException as http_exc:
            raise http_exc
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured {e}")
        
    @staticmethod
    def get_vehicle_fee(vehicle_id: int, db: Session, rate_per_hour: int = 50):
        try:
            vehicle = db.exec(select(VehicleRegistration).where(VehicleRegistration.id == vehicle_id)).first()

            if not vehicle:
                raise HTTPException(status_code=404, detail="Vehicle not found.")

            vehicle.exit_time = datetime.now(timezone.utc)

            if vehicle.exit_time and vehicle.entry_time:
                duration = vehicle.exit_time - vehicle.entry_time
                hours_parked = max(1, duration.total_seconds() // 3600)
                parking_fee = int(hours_parked * rate_per_hour)
            else:
                parking_fee = 50

            entry_time_pst = vehicle.entry_time.astimezone(PST) if vehicle.entry_time else None
            exit_time_pst = vehicle.exit_time.astimezone(PST) if vehicle.exit_time else None

            formatted_entry_time = entry_time_pst.strftime("%I:%M %p") if entry_time_pst else None
            formatted_exit_time = exit_time_pst.strftime("%I:%M %p") if exit_time_pst else None

            return {
                "vehicle_number": vehicle.vehicle_number,
                "parking_spot_id": vehicle.parking_spot_id,
                "exit_time": formatted_exit_time,
                "entry_time": formatted_entry_time, 
                "parking_fee": parking_fee
                }
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured {e}")
    
class VehicleRegistrationController:
    waiting_queue=deque()
    
    @staticmethod
    def create_vehicle_registration(vehicle_registration: VehicleRegistration,db:Session):
        try:
            existing_vehicle = db.exec(
            select(VehicleRegistration).where(VehicleRegistration.vehicle_number == vehicle_registration.vehicle_number)
            ).first()

            if existing_vehicle:
                raise HTTPException(status_code=400, detail="Vehicle is already registered.")

            available_spot = db.exec(
            select(ParkingSpot).where(ParkingSpot.status == "available")
            ).first()    
            
            if not available_spot:
                VehicleRegistrationController.waiting_queue.append(vehicle_registration)
                raise HTTPException(status_code=400, detail="All slots are full. Your vehicle are added to the queue.")
            
            available_spot.status="occupied"
            vehicle_registration.parking_spot_id = available_spot.id
    
            db.add(vehicle_registration)
            db.commit()
            db.refresh(vehicle_registration)
            return vehicle_registration
        
        
        except HTTPException as http_exc:
            raise http_exc
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured {e}")

    @staticmethod
    def read_vehicle_registrations(db:Session):
        try:
            statement = select(VehicleRegistration, ParkingSpot).join(ParkingSpot, VehicleRegistration.parking_spot_id == ParkingSpot.id)
            results = db.exec(statement).all()

            parking_fee=50
            vehicle_registrations = []
            for vehicle, spot in results:
                entry_time = vehicle.entry_time
                exit_time = vehicle.exit_time
            
                if entry_time and exit_time:
                    duration = exit_time - vehicle.entry_time
                    hours_parked = math.ceil(duration.total_seconds() // 3600)
                    parking_fee = int(hours_parked * 50)  

                formatted_entry_time = entry_time.strftime("%I:%M %p") if entry_time else None
                formatted_exit_time = exit_time.strftime("%I:%M %p")   if exit_time else None

                vehicle_registration = {
                    "id": vehicle.id,
                    "vehicle_number": vehicle.vehicle_number,
                    "entry_time": formatted_entry_time,
                    "exit_time": formatted_exit_time,
                    "parking_fee": parking_fee,
                    "parking_spot": {
                        "id": spot.id,
                        "slot": spot.slot,
                        "status": spot.status 
                    }
                }
                vehicle_registrations.append(vehicle_registration)

            return vehicle_registrations
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured {e}")


    @staticmethod
    def process_waiting_queue(db:Session = Depends(get_db)):
        try:
            if VehicleRegistrationController.waiting_queue:
                next_vehicle= VehicleRegistrationController.waiting_queue.popleft()
            
            available_spot = db.exec(
                    select(ParkingSpot).where(ParkingSpot.status == "available")
            ).first()

            if available_spot:
                available_spot.status = "occupied"
                next_vehicle.parking_spot_id = available_spot.id
                db.add(next_vehicle)
                db.commit()

                return next_vehicle    
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured {e}")
           
    @staticmethod
    def delete_vehicle_registration(slot_number: int, db:Session,rate_per_hour: int = 50):
        try:
            parking_spot = db.exec(select(ParkingSpot).where(ParkingSpot.slot == slot_number)).first()

            if not parking_spot or parking_spot.status != "occupied":
                raise HTTPException(status_code=404, detail="Parking spot is not occupied or does not exist.")

            vehicle = db.exec(select(VehicleRegistration).where(VehicleRegistration.parking_spot_id == parking_spot.id)).first()

            if not vehicle:
                raise HTTPException(status_code=404, detail="Vehicle registration not found.")

            vehicle.exit_time = datetime.now(timezone.utc)
            entry_time_aware = vehicle.entry_time if vehicle.entry_time.tzinfo else vehicle.entry_time.replace(tzinfo=timezone.utc)
            exit_time_aware = vehicle.exit_time

            if exit_time_aware and entry_time_aware:
                duration = exit_time_aware - entry_time_aware
                hours_parked = math.ceil(duration.total_seconds() // 3600)
                parking_fee = int(hours_parked * rate_per_hour)
            else:
                parking_fee = 50

            entry_time_pst = entry_time_aware.astimezone(PST) if vehicle.entry_time else None
            exit_time_pst = exit_time_aware.astimezone(PST) if vehicle.exit_time else None
            formatted_entry_time = entry_time_pst.strftime("%I:%M %p") if entry_time_pst else None
            formatted_exit_time = exit_time_pst.strftime("%I:%M %p") if exit_time_pst else None

            response_data = {
            "vehicle_number": vehicle.vehicle_number,
            "entry_time": formatted_entry_time,
            "exit_time": formatted_exit_time,
            "parking_fee": parking_fee
        }

            parking_spot.status = "available"
            db.add(parking_spot)

            db.delete(vehicle)
            db.commit()

            return {
            "message": f"Vehicle registration in slot {slot_number} has been deleted.",
            "vehicle_details": response_data
            }
        
        except HTTPException as http_exc:
            raise http_exc
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured {e}")

    @staticmethod
    def get_all_vehicle_records(db:Session):
        try:
            statement = select(VehicleRegistration, ParkingSpot).join(ParkingSpot, VehicleRegistration.parking_spot_id == ParkingSpot.id)
            results = db.exec(statement).all()

            vehicle_records = []

            for vehicle, spot in results:
                entry_time = vehicle.entry_time
                exit_time = vehicle.exit_time

            if vehicle.entry_time and exit_time:
                duration = exit_time - vehicle.entry_time
                hours_parked = math.ceil( duration.total_seconds() // 3600)
                parking_fee = int(hours_parked * 50)
            else:
                parking_fee = 50

            formatted_entry_time = entry_time.strftime("%I:%M %p") if entry_time else None
            formatted_exit_time = exit_time.strftime("%I:%M %p") if exit_time else None

            vehicle_record = {
                "id": vehicle.id,
                "vehicle_number": vehicle.vehicle_number,
                "entry_time": formatted_entry_time,
                "exit_time": formatted_exit_time,
                "parking_fee": parking_fee,
                "status": "exited" if exit_time else "parked",
                "parking_spot": {
                    "id": spot.id,
                    "slot": spot.slot,
                    "status": spot.status
                }
            }
            vehicle_records.append(vehicle_record)

            for vehicle in VehicleRegistrationController.waiting_queue:
                vehicle_record = {
                "vehicle_number": vehicle.vehicle_number,
                "status": "in queue",
                "entry_time": None,
                "exit_time": None,
                "parking_spot": None,
                "parking_fee": None
                }
            vehicle_records.append(vehicle_record)

            return vehicle_records
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured  {e}")
