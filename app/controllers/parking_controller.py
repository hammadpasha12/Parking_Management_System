from datetime import datetime, timezone
from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.parking_spot import ParkingSpot,VehicleRegistration
from app.database import engine

class ParkingController:
    @staticmethod
    def create_parking_spot(parking_spot: ParkingSpot):
        if parking_spot.slot > 20:
            raise HTTPException(status_code=400, detail="Slot number cannot exceed 20.")
        with Session(engine) as session:
            existing_spot = session.exec(select(ParkingSpot).where(ParkingSpot.slot == parking_spot.slot)).first()
            if existing_spot:
                raise HTTPException(status_code=400, detail="Slot is already filled.")
            
            session.add(parking_spot)
            session.commit()
            session.refresh(parking_spot)
            return parking_spot

    @staticmethod
    def read_parking_spots():
        with Session(engine) as session:
            return session.exec(select(ParkingSpot)).all()
    
    @staticmethod
    def delete_parking_spot(slot_id: int):
        with Session(engine) as session:
            spot_del = session.exec(select(ParkingSpot).where(ParkingSpot.id == slot_id)).first()
            if not spot_del:
                raise HTTPException(status_code=404, detail="Slot not found.")
            
            session.delete(spot_del)
            session.commit()
            return {"message": f"Parking spot {slot_id} has been deleted."}
        
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
                parking_fee = 0  

            formatted_entry_time = vehicle.entry_time.strftime("%I:%M %p")
            formatted_exit_time = vehicle.exit_time.strftime("%I:%M %p")

            return {
                "vehicle_number": vehicle.vehicle_number,
                "parking_spot_id": vehicle.parking_spot_id,
                "exit_time": formatted_exit_time,
                "entry_time": formatted_entry_time,
                "parking_fee": parking_fee
            }
    
class VehicleRegistrationController:
    @staticmethod
    def create_vehicle_registration(vehicle_registration: VehicleRegistration):
        with Session(engine) as session:
            existing_vehicle = session.exec(
                select(VehicleRegistration).where(VehicleRegistration.vehicle_number == vehicle_registration.vehicle_number)
            ).first()

            if existing_vehicle:
                raise HTTPException(status_code=400, detail="Vehicle is already registered.")

            parking_spot = session.exec(
                select(ParkingSpot).where(ParkingSpot.id == vehicle_registration.parking_spot_id)
            ).first()
            
            if not parking_spot:
                raise HTTPException(status_code=404, detail="Parking spot not found.")
            
            if parking_spot.status == "occupied":
                raise HTTPException(status_code=400, detail="Parking spot is already occupied.")

            parking_spot.status = "occupied"
            
            session.add(vehicle_registration)
            session.commit()
            session.refresh(vehicle_registration)
            return vehicle_registration

    @staticmethod
    def read_vehicle_registrations():
        with Session(engine) as session:
            statement = select(VehicleRegistration, ParkingSpot).join(ParkingSpot, VehicleRegistration.parking_spot_id == ParkingSpot.id)
            results = session.exec(statement).all()

        vehicle_registrations = []
        for vehicle, spot in results:
            exit_time = vehicle.exit_time if vehicle.exit_time else None
            parking_fee = 0
            
            if vehicle.entry_time and exit_time:
                duration = exit_time - vehicle.entry_time
                hours_parked = max(1, duration.total_seconds() // 3600)
                parking_fee = int(hours_parked * 50)  
            else:
                parking_fee=50    

            vehicle_registration = {
                "id": vehicle.id,
                "vehicle_number": vehicle.vehicle_number,
                "entry_time": vehicle.entry_time,
                "exit_time": exit_time,
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
    def delete_vehicle_registration(vehicle_id: int):
        with Session(engine) as session:
            vehicle = session.exec(select(VehicleRegistration).where(VehicleRegistration.id == vehicle_id)).first()

            if not vehicle:
                raise HTTPException(status_code=404, detail="Vehicle registration not found.")

            parking_spot = session.exec(
                select(ParkingSpot).where(ParkingSpot.id == vehicle.parking_spot_id)
            ).first()
            
            if parking_spot:
                parking_spot.status = "available"
            
            session.delete(vehicle)
            session.commit()

            return {"message": f"Vehicle registration {vehicle_id} has been deleted."}