from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import random

router = APIRouter()

class RouteRequest(BaseModel):
    start_location: str
    end_location: str
    travel_mode: Optional[str] = 'car'
    arrival_time: str

@router.post('/optimize')
async def optimize_route(request: RouteRequest):
    """
    Optimize route based on traffic predictions
    """
    routes = [
        {
            'route_id': 'A',
            'name': 'Fastest Route',
            'distance': round(random.uniform(8.5, 12.3), 2),
            'duration': random.randint(22, 35),
            'traffic_level': 'medium',
            'efficiency_score': random.randint(85, 95),
            'co2_savings': round(random.uniform(0.8, 1.5), 2),
            'waypoints': [
                {'lat': 40.758, 'lng': -73.9855},
                {'lat': 40.770, 'lng': -73.975},
                {'lat': 40.785, 'lng': -73.968}
            ]
        },
        {
            'route_id': 'B',
            'name': 'Scenic Route',
            'distance': round(random.uniform(10.2, 14.1), 2),
            'duration': random.randint(28, 42),
            'traffic_level': 'low',
            'efficiency_score': random.randint(70, 84),
            'co2_savings': round(random.uniform(0.5, 1.2), 2),
            'waypoints': [
                {'lat': 40.758, 'lng': -73.9855},
                {'lat': 40.765, 'lng': -73.980},
                {'lat': 40.785, 'lng': -73.968}
            ]
        }
    ]
    
    return {
        'success': True,
        'routes': routes,
        'recommended_route': 'A',
        'departure_time': request.arrival_time,
        'travel_mode': request.travel_mode
    }

@router.get('/alternatives')
async def get_alternative_routes():
    """
    Get alternative route suggestions
    """
    return {
        'success': True,
        'alternatives': [
            {'mode': 'car', 'duration': random.randint(25, 35)},
            {'mode': 'bike', 'duration': random.randint(35, 50)},
            {'mode': 'transit', 'duration': random.randint(40, 55)}
        ]
    }
