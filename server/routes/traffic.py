from fastapi import APIRouter
from pydantic import BaseModel
import random
from datetime import datetime, timedelta

router = APIRouter()

class TrafficRequest(BaseModel):
    start_location: str
    end_location: str
    departure_time: str

@router.post('/predict')
async def predict_traffic(request: TrafficRequest):
    """
    Predict traffic congestion for a given route and time
    """
    traffic_levels = []
    current_time = datetime.strptime(request.departure_time, '%H:%M')
    
    for i in range(12):
        time_slot = current_time + timedelta(minutes=i*15)
        hour = time_slot.hour + time_slot.minute / 60
        
        if 7.5 <= hour <= 9:
            congestion = random.randint(70, 95)
            level = 'high'
        elif 6 <= hour < 7.5 or 9 < hour <= 10:
            congestion = random.randint(45, 70)
            level = 'medium'
        else:
            congestion = random.randint(20, 45)
            level = 'low'
        
        traffic_levels.append({
            'time': time_slot.strftime('%H:%M'),
            'congestion_index': congestion,
            'level': level
        })
    
    return {
        'success': True,
        'route': {
            'start': request.start_location,
            'end': request.end_location
        },
        'predictions': traffic_levels,
        'recommended_departure': (current_time - timedelta(minutes=20)).strftime('%H:%M'),
        'estimated_travel_time': random.randint(35, 65)
    }

@router.get('/current')
async def get_current_traffic():
    """
    Get current traffic status
    """
    return {
        'success': True,
        'current_congestion': random.randint(60, 85),
        'level': random.choice(['low', 'medium', 'high']),
        'timestamp': datetime.now().isoformat()
    }
