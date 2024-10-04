from datetime import datetime, timezone
from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.parking_spot import ParkingSpot,VehicleRegistration
from app.database import engine
import pytz
from collections import deque

PST = pytz.timezone('Asia/Karachi')


class ParkingController:
    @staticmethod
    def create_parking_spot(parking_spot: ParkingSpot):
        if parking_spot.slot > 20:
            raise HTTPException(status_code=400, detail="Slot number cannot exceed 20.")
        with Session(engine) as session:    
            existing_spot = session.exec(select(ParkingSpot).where(ParkingSpot.slot == parking_spot.slot)).first()
            if existing_spot:
                raise HTTPException(status_code=400, detail="Slot is already filled.")
            
            new_spot = ParkingSpot(slot=parking_spot.slot, status="available")
            print("new spot====>",new_spot)
            session.add(new_spot)
            session.commit()
            session.refresh(new_spot)
            return new_spot

    @staticmethod
    def read_parking_spots():
        with Session(engine) as session:
            parking_spots = session.exec(select(ParkingSpot)).all()
            return parking_spots
    
    @staticmethod
    def delete_parking_spot(slot_id: int):
        with Session(engine) as session:
            spot_del = session.exec(select(ParkingSpot).where(ParkingSpot.id == slot_id)).first()
            if not spot_del:
                raise HTTPException(status_code=404, detail="Slot not found.")
            
            session.delete(spot_del)
            spot_del.status = "available"
            session.commit()

            next_vehicle = VehicleRegistrationController.process_waiting_queue()

            if next_vehicle:
                return{"message":f"Slot {slot_id} is now available and assigned to the next vehicle in the queue."}
            
            return {"message": f"Parking spot {slot_id} has been deleted and is now available."}
        
    @staticmethod
    def get_vehicle_fee(vehicle_id: int, rate_per_hour: int = 50):
        with Session(engine) as session:
            vehicle = session.exec(select(VehicleRegistration).where(VehicleRegistration.id == vehicle_id)).first()
            
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
    
class VehicleRegistrationController:

    waiting_queue=deque()

    @staticmethod
    def create_vehicle_registration(vehicle_registration: VehicleRegistration):
        with Session(engine) as session:
            existing_vehicle = session.exec(
                select(VehicleRegistration).where(VehicleRegistration.vehicle_number == vehicle_registration.vehicle_number)
            ).first()

            if existing_vehicle:
                raise HTTPException(status_code=400, detail="Vehicle is already registered.")

            available_spot = session.exec(
                select(ParkingSpot).where(ParkingSpot.status == "available")
            ).first()    
            
            if not available_spot:
                VehicleRegistrationController.waiting_queue.append(vehicle_registration)
                raise HTTPException(status_code=400, detail="All slots are full. Your vehicle are added to the queue.")
            
            available_spot.status="occupied"
            vehicle_registration.parking_spot_id = available_spot.id

            
            session.add(vehicle_registration)
            session.commit()
            session.refresh(vehicle_registration)
            return vehicle_registration

    @staticmethod
    def read_vehicle_registrations():
        with Session(engine) as session:
            statement = select(VehicleRegistration, ParkingSpot).join(ParkingSpot, VehicleRegistration.parking_spot_id == ParkingSpot.id)
            results = session.exec(statement).all()

        parking_fee=50
        vehicle_registrations = []
        for vehicle, spot in results:
            entry_time = vehicle.entry_time
            exit_time = vehicle.exit_time
            
            if vehicle.entry_time and exit_time:
                duration = exit_time - vehicle.entry_time
                hours_parked = max(1, duration.total_seconds() // 3600)
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


    @staticmethod
    def process_waiting_queue():
        if VehicleRegistrationController.waiting_queue:
            next_vehicle= VehicleRegistrationController.waiting_queue.popleft()
            
            with Session(engine) as session:
                available_spot = session.exec(
                    select(ParkingSpot).where(ParkingSpot.status == "available")
                ).first()

                if available_spot:
                    available_spot.status = "occupied"
                    next_vehicle.parking_spot_id = available_spot.id
                    session.add(next_vehicle)
                    session.commit()

                return next_vehicle    
            
    @staticmethod
    def delete_vehicle_registration(vehicle_id: int, rate_per_hour: int = 50):
        with Session(engine) as session:
            vehicle = session.exec(select(VehicleRegistration).where(VehicleRegistration.id == vehicle_id)).first()

        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle registration not found.")

        vehicle.exit_time = datetime.now(timezone.utc)
        entry_time_aware = vehicle.entry_time if vehicle.entry_time.tzinfo else vehicle.entry_time.replace(tzinfo=timezone.utc)
        exit_time_aware = vehicle.exit_time

        if exit_time_aware and entry_time_aware:
            duration = exit_time_aware - entry_time_aware
            hours_parked = max(1, duration.total_seconds() // 3600)
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
        
        parking_spot = session.exec(select(ParkingSpot).where(ParkingSpot.id == vehicle.parking_spot_id)).first()
        if parking_spot:
            parking_spot.status= "available"


        session.delete(vehicle)
        session.commit()

        return {
            "message": f"Vehicle registration {vehicle_id} has been deleted.",
            "vehicle_details": response_data
        }
