from flask import Flask, request, jsonify, render_template
from utils import (
    get_coordinates,
    get_solar_position,
    calculate_shadow_length,
    calculate_confidence,
    get_street_width,
    generate_nearby_coordinates,
    estimate_building_height,
    reverse_geocode
)
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sunlight', methods=['POST'])
def sunlight_estimation():
    data = request.json
    location = data.get('location')
    radius = data.get('radius_meters', 500)  # Default radius 500 meters

    if not location:
        return jsonify({'error': 'Location is required.'}), 400

    # Step 1: Geocoding
    try:
        lat, lon = get_coordinates(location)
    except Exception as e:
        return jsonify({'error': f'Geocoding failed: {str(e)}'}), 500

    # Step 2: Solar Position
    try:
        elevation, azimuth, sunrise, sunset = get_solar_position(lat, lon)
    except Exception as e:
        return jsonify({'error': f'Solar position calculation failed: {str(e)}'}), 500

    # Step 3: Building Height Estimation
    try:
        building_height = estimate_building_height(lat, lon)
    except Exception as e:
        building_height = 15  # Default approximation (e.g., 5 floors * 3m)
    
    # Step 4: Street Width Estimation
    try:
        street_width = get_street_width(lat, lon)
    except Exception as e:
        street_width = 10  # Default approximation in meters

    # Step 5: Shadow Length Calculation
    shadow_length = calculate_shadow_length(building_height, elevation)

    # Step 6: Confidence Calculation
    sunlight_present, confidence = calculate_confidence(elevation, shadow_length, street_width)

    # Step 7: Nearby Sunny Spot Suggestions
    nearby_sunny_locations = []
    if sunlight_present:
        current_location_name = reverse_geocode(lat, lon)
    else:
        current_location_name = reverse_geocode(lat, lon)

    # Generate nearby coordinates
    nearby_coords = generate_nearby_coordinates(lat, lon, radius=radius, interval=45)
    
    for coord in nearby_coords:
        n_lat, n_lon = coord
        try:
            n_elevation, n_azimuth, _, _ = get_solar_position(n_lat, n_lon)
            n_building_height = estimate_building_height(n_lat, n_lon)
            n_street_width = get_street_width(n_lat, n_lon)
            n_shadow_length = calculate_shadow_length(n_building_height, n_elevation)
            n_sunlight, n_confidence = calculate_confidence(n_elevation, n_shadow_length, n_street_width)
            if n_sunlight:
                location_name = reverse_geocode(n_lat, n_lon)
                nearby_sunny_locations.append({
                    'location_name': location_name,
                    'coordinates': {'latitude': n_lat, 'longitude': n_lon},
                    'sunlight_status': n_sunlight,
                    'confidence_level': round(n_confidence, 2)
                })
        except:
            continue  # Skip if any calculation fails

    # Sort and select top 5
    nearby_sunny_locations = sorted(nearby_sunny_locations, key=lambda x: x['confidence_level'], reverse=True)[:5]

    response = {
        'current_sunlight_status': sunlight_present,
        'confidence_level': round(confidence, 2),
        'nearby_sunny_locations': nearby_sunny_locations
    }

    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True)
