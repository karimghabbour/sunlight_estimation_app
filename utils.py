import math
from geopy.geocoders import Nominatim
from suntime import Sun, SunTimeException
from datetime import datetime
import requests

def get_coordinates(location_name):
    geolocator = Nominatim(user_agent="sunlight_app")
    location = geolocator.geocode(location_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        raise ValueError("Location not found.")

def get_solar_position(lat, lon):
    sun = Sun(lat, lon)
    now = datetime.utcnow()
    elevation = sun.get_altitude(now)
    azimuth = sun.get_azimuth(now)
    sunrise = sun.get_local_sunrise_time()
    sunset = sun.get_local_sunset_time()
    return elevation, azimuth, sunrise, sunset

def calculate_shadow_length(building_height, solar_elevation_deg):
    if solar_elevation_deg <= 0:
        return float('inf')  # No sunlight
    solar_elevation_rad = math.radians(solar_elevation_deg)
    return building_height / math.tan(solar_elevation_rad)

def calculate_confidence(solar_elevation, shadow_length, street_width):
    if solar_elevation <= 0:
        return False, 0.0
    ratio = shadow_length / street_width
    confidence = (solar_elevation / 90) * (1 - ratio)
    confidence = max(min(confidence, 1.0), 0.0)
    sunlight_present = shadow_length < street_width
    return sunlight_present, confidence

def get_street_width(lat, lon):
    # Using OpenStreetMap Overpass API to estimate street width
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    way(around:50,{lat},{lon})["highway"];
    out body;
    """
    response = requests.get(overpass_url, params={'data': query})
    data = response.json()
    
    # Simplified estimation: count number of ways as an indicator
    if 'elements' in data:
        street_count = len(data['elements'])
        # Approximate street width based on street_count
        # This is a placeholder; real implementation would parse tags for actual width
        if street_count > 10:
            return 12  # Wider streets in busy areas
        else:
            return 8  # Narrower streets
    return 10  # Default approximation

def estimate_building_height(lat, lon):
    # Placeholder function: In real implementation, fetch building height from GIS data
    # Here, we use a heuristic based on location or randomization
    # For demonstration, return a default value
    return 15  # meters (e.g., 5 floors * 3m)

def generate_nearby_coordinates(lat, lon, radius=500, interval=45):
    from geopy.distance import geodesic
    from geopy.point import Point
    directions = range(0, 360, interval)
    nearby_coords = []
    origin = Point(lat, lon)
    for bearing in directions:
        destination = geodesic(meters=radius).destination(origin, bearing)
        nearby_coords.append((destination.latitude, destination.longitude))
    return nearby_coords

def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="sunlight_app")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    if location:
        return location.address
    else:
        return "Unknown Location"
