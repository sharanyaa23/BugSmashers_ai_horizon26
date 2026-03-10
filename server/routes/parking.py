from fastapi import APIRouter
from pydantic import BaseModel
import random

router = APIRouter()

class ParkingRequest(BaseModel):
    destination: str
    arrival_time: str

@router.post('/predict')
async def predict_parking(request: ParkingRequest):
    """
    Predict parking availability at destination
    """
    parking_zones = [
        {
            'id': 1,
            'name': 'Metro Parking Lot',
            'distance': 0.2,
            'availability': random.randint(55, 85),
            'price_per_hour': 8,
            'total_spots': 150,
            'available_spots': random.randint(60, 120),
            'location': {'lat': 40.784, 'lng': -73.967}
        },
        {
            'id': 2,
            'name': 'City Mall Parking',
            'distance': 0.4,
            'availability': random.randint(40, 70),
            'price_per_hour': 12,
            'total_spots': 200,
            'available_spots': random.randint(80, 140),
            'location': {'lat': 40.786, 'lng': -73.965}
        },
        {
            'id': 3,
            'name': 'Central Plaza Garage',
            'distance': 0.6,
            'availability': random.randint(30, 60),
            'price_per_hour': 6,
            'total_spots': 100,
            'available_spots': random.randint(30, 60),
            'location': {'lat': 40.783, 'lng': -73.970}
        }
    ]
    
    overall_probability = sum(z['availability'] for z in parking_zones) / len(parking_zones)
    
    return {
        'success': True,
        'destination': request.destination,
        'overall_probability': round(overall_probability, 1),
        'parking_zones': parking_zones,
        'recommendation': 'Arrive before 5:00 PM for best availability'
    }

@router.get('/availability/{zone_id}')
async def get_zone_availability(zone_id: int):
    """
    Get real-time availability for specific parking zone
    """
    return {
        'success': True,
        'zone_id': zone_id,
        'available_spots': random.randint(20, 100),
        'last_updated': 'Just now'
    }
