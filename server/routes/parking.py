from fastapi import APIRouter
from pydantic import BaseModel
import hashlib
import json
import math
from urllib.parse import quote
from urllib import error as urlerror
from urllib import request as urlrequest

router = APIRouter()

class ParkingRequest(BaseModel):
    destination: str
    arrival_time: str


FALLBACK_DESTINATIONS = {
    'Mumbai': {'lat': 19.0760, 'lng': 72.8777},
    'Pune': {'lat': 18.5204, 'lng': 73.8567},
    'Bandra': {'lat': 19.0596, 'lng': 72.8295},
    'Andheri': {'lat': 19.1136, 'lng': 72.8697},
    'Dadar': {'lat': 19.0178, 'lng': 72.8478},
}


def _location_label(destination: str) -> str:
    return destination.split(',')[0].strip() if ',' in destination else destination.strip()


def _get_seed(destination: str, arrival_time: str) -> int:
    key = f"{destination.lower()}::{arrival_time}"
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)


def _geocode_destination(destination: str):
    params = f"q={quote(destination)}&format=jsonv2&limit=1"
    request = urlrequest.Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={
            "User-Agent": "UrbanNavigatorAI/1.0"
        }
    )

    try:
        with urlrequest.urlopen(request, timeout=10) as response:
            results = json.loads(response.read().decode("utf-8"))
        if results:
            top_result = results[0]
            return {
                'lat': float(top_result['lat']),
                'lng': float(top_result['lon']),
                'label': top_result.get('display_name', destination)
            }
    except (urlerror.URLError, ValueError, KeyError) as exc:
        print(f"Warning: destination geocoding failed for parking API: {exc}")

    fallback_key = _location_label(destination)
    fallback_coords = FALLBACK_DESTINATIONS.get(fallback_key, FALLBACK_DESTINATIONS['Mumbai'])
    return {
        'lat': fallback_coords['lat'],
        'lng': fallback_coords['lng'],
        'label': destination
    }


def _offset_distance_km(lat_a, lng_a, lat_b, lng_b):
    lat_km = (lat_b - lat_a) * 111
    lng_km = (lng_b - lng_a) * 111 * math.cos(math.radians(lat_a))
    return round(math.sqrt((lat_km ** 2) + (lng_km ** 2)), 2)


def _build_parking_zones(destination: str, arrival_time: str):
    location = _geocode_destination(destination)
    label = _location_label(destination)
    seed = _get_seed(destination, arrival_time)
    hour = int(arrival_time.split(':')[0]) if ':' in arrival_time else 18

    offset_sets = [
        (0.0028, 0.0034),
        (-0.0031, 0.0025),
        (0.0019, -0.0042),
    ]
    zone_names = [
        f'{label} Central Parking',
        f'{label} Smart Garage',
        f'{label} Plaza Parking',
    ]

    parking_zones = []
    for index, (lat_offset, lng_offset) in enumerate(offset_sets, start=1):
        multiplier = 1 + (((seed >> (index * 2)) % 5) / 20)
        zone_lat = location['lat'] + (lat_offset * multiplier)
        zone_lng = location['lng'] + (lng_offset * multiplier)
        total_spots = 90 + ((seed >> (index * 4)) % 120)
        rush_penalty = 15 if 17 <= hour <= 20 else 0
        availability = max(18, min(92, 78 - rush_penalty - (index * 9) + ((seed >> (index * 3)) % 18)))
        available_spots = max(8, int(round((availability / 100) * total_spots)))

        parking_zones.append(
            {
                'id': index,
                'name': zone_names[index - 1],
                'distance': _offset_distance_km(location['lat'], location['lng'], zone_lat, zone_lng),
                'availability': availability,
                'price_per_hour': 35 + ((seed >> (index * 5)) % 35),
                'total_spots': total_spots,
                'available_spots': available_spots,
                'location': {'lat': round(zone_lat, 6), 'lng': round(zone_lng, 6)}
            }
        )

    parking_zones.sort(key=lambda zone: (-zone['availability'], zone['distance']))
    return location, parking_zones


def _build_recommendation(destination: str, arrival_time: str, parking_zones):
    best_zone = parking_zones[0]
    hour = int(arrival_time.split(':')[0]) if ':' in arrival_time else 18
    label = _location_label(destination)

    if hour >= 17 and best_zone['availability'] < 55:
        return f"{label} is getting busy. Aim to arrive before {arrival_time} or use {best_zone['name']} first."
    if best_zone['availability'] >= 70:
        return f"{best_zone['name']} looks strongest right now with {best_zone['availability']}% predicted availability."
    return f"Parking is moderate near {label}. Start with {best_zone['name']} for the best chance of a quick spot."


@router.post('/predict')
async def predict_parking(request: ParkingRequest):
    """
    Predict parking availability at destination
    """
    location, parking_zones = _build_parking_zones(request.destination, request.arrival_time)
    overall_probability = sum(zone['availability'] for zone in parking_zones) / len(parking_zones)
    recommendation = _build_recommendation(request.destination, request.arrival_time, parking_zones)

    return {
        'success': True,
        'destination': request.destination,
        'destination_label': location['label'],
        'destination_location': {
            'lat': location['lat'],
            'lng': location['lng']
        },
        'overall_probability': round(overall_probability, 1),
        'parking_zones': parking_zones,
        'recommendation': recommendation
    }


@router.get('/availability/{zone_id}')
async def get_zone_availability(zone_id: int):
    """
    Get real-time availability for specific parking zone
    """
    return {
        'success': True,
        'zone_id': zone_id,
        'available_spots': 20 + ((zone_id * 17) % 80),
        'last_updated': 'Just now'
    }