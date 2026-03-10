from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta

base_path = Path(__file__).parent.parent
sys.path.append(str(base_path))

from departure_optimizer import recommend_departure

router = APIRouter()

class RouteRequest(BaseModel):
    start_location: str
    end_location: str
    travel_mode: Optional[str] = 'car'
    arrival_time: str

@router.post('/optimize')
async def optimize_route(request: RouteRequest):
    """
    Optimize route using Member 2's traffic predictions + Member 3's departure optimizer
    """
    try:
        import requests
        
        base_time = datetime.strptime(request.arrival_time, '%H:%M')
        traffic_predictions = {}
        
        for i in range(-4, 5):
            time_offset = base_time + timedelta(minutes=i * 10)
            time_str = time_offset.strftime('%H:%M')
            
            try:
                response = requests.post(
                    'http://localhost:8000/api/traffic/predict',
                    json={
                        'start_location': request.start_location,
                        'end_location': request.end_location,
                        'departure_time': time_str
                    },
                    timeout=2
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('predictions_1hr'):
                        avg_level = data['predictions_1hr'][0]['level']
                        traffic_predictions[time_str] = avg_level.capitalize()
                else:
                    traffic_predictions[time_str] = 'Medium'
            except:
                hour = time_offset.hour + time_offset.minute / 60
                if 7.5 <= hour <= 9 or 17 <= hour <= 19:
                    traffic_predictions[time_str] = 'High'
                elif 6 <= hour < 7.5 or 9 < hour <= 10:
                    traffic_predictions[time_str] = 'Medium'
                else:
                    traffic_predictions[time_str] = 'Low'
        
        best_departure = recommend_departure(traffic_predictions)
        
        routes = [
            {
                'route_id': 'A',
                'name': 'Optimal Route (AI Recommended)',
                'distance': round(random.uniform(8.5, 12.3), 2),
                'duration': int(best_departure['Estimated Travel Time']),
                'traffic_level': best_departure['Traffic Level'].lower(),
                'efficiency_score': 95 if best_departure['Traffic Level'] == 'Low' else 75,
                'co2_savings': round(random.uniform(1.2, 2.0), 2),
                'departure_time': best_departure['Departure Time'],
                'waypoints': [
                    {'lat': 40.758, 'lng': -73.9855},
                    {'lat': 40.770, 'lng': -73.975},
                    {'lat': 40.785, 'lng': -73.968}
                ]
            },
            {
                'route_id': 'B',
                'name': 'Alternative Route',
                'distance': round(random.uniform(10.2, 14.1), 2),
                'duration': random.randint(35, 50),
                'traffic_level': 'medium',
                'efficiency_score': random.randint(70, 84),
                'co2_savings': round(random.uniform(0.5, 1.2), 2),
                'departure_time': request.arrival_time,
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
            'optimal_departure': {
                'time': best_departure['Departure Time'],
                'traffic_level': best_departure['Traffic Level'],
                'estimated_travel_time': int(best_departure['Estimated Travel Time'])
            },
            'traffic_predictions': traffic_predictions,
            'travel_mode': request.travel_mode,
            'model_info': 'Using Hugging Face Chronos T5 + Departure Optimizer'
        }
    except Exception as e:
        print(f"Error in route optimization: {e}")
        return {
            'success': False,
            'error': str(e),
            'routes': [],
            'recommended_route': None
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
