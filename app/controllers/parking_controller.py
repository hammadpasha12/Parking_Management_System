from sqlmodel import Session, select
from fastapi import HTTPException
from app.models.parking_spot import ParkingSpot
from app.database import engine

class ParkingController:
    
    @staticmethod
    def create_parking_spot(parking_spot: ParkingSpot):
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
