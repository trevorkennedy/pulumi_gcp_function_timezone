"""
Run locally:
  pip install functions-framework
  cd functions/
  functions-framework --target get_demo --port 5000

Deploy:
  pulumi up
"""

import os
import json
from flask import jsonify
from math import sin, cos, sqrt, atan2, radians


def calc_distance(src_lat, src_lng, dest_lat, dest_lng):
    lat1 = radians(src_lat)
    lon1 = radians(src_lng)
    lat2 = radians(dest_lat)
    lon2 = radians(dest_lng)
    d_lon = lon2 - lon1
    d_lat = lat2 - lat1
    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return 6373.0 * c


def load_json(filename):
    with open(filename) as f:
        return json.load(f)


def find_min_distance(filename, label, lat, lng):
    min_distance = 100000.0
    min_value = None
    if lat == 0.0 and lng == 0.0:
        return min_value

    cities = load_json(filename)
    for city in cities:
        if city['lat'] != 0 and city['lng'] != 0:
            distance = calc_distance(city['lat'], city['lng'], lat, lng)
            if distance < min_distance:
                min_distance = distance
                min_value = city[label]
                if distance < 50:
                    return min_value
    return None if min_distance > 1000 else min_value


def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true'
    }


def preflight_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Authorization',
        'Access-Control-Max-Age': '3600',
    }


def get_header(request, header):
    if header in request.headers:
        return request.headers[header]
    else:
        return ''


def get_demo(request):
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request
    # Set CORS headers for preflight requests
    if request.method == 'OPTIONS':
        # Allows GET requests from origin * with Authorization header
        return ('', 204, preflight_headers())

    lat = 0.0
    lng = 0.0
    cityLatLong = get_header(request, 'X-Appengine-CityLatLong')
    if cityLatLong != '':
        lat = float(cityLatLong.split(',')[0])
        lng = float(cityLatLong.split(',')[1])

    timezone = find_min_distance('cityMap.json', 'timezone', lat, lng)
    metro = find_min_distance('metros.json', 'name', lat, lng)

    # JSON response
    data = {
        'MY_VAR': os.getenv("MY_VAR", "default"),
        'path': request.path,
        'args': request.args,
        'Country': get_header(request, 'X-Appengine-Country'),
        'Region': get_header(request, 'X-Appengine-Region').upper(),
        'City': get_header(request, 'X-Appengine-City').title(),
        'User-IP': get_header(request, 'X-Appengine-User-IP'),
        'Timezone': '' if timezone is None else timezone,
        'Metro': 'International' if metro is None else metro,
        'Lat': lat,
        'Lng': lng
    }

    return jsonify(data), 200, cors_headers()
