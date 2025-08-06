import pandas as pd
from geopy.geocoders import GoogleV3
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

# ✅ Insert your Google Maps Geocoding API key here
geolocator = GoogleV3(api_key="AIzaSyDgFdD4VOsPjHXTEZElpA3OYLsJEIMhR_0")

def load_data(file_path="datamanifest.csv"):
    df = pd.read_csv(file_path, dtype={'Barcode': str})
    df['Barcode'] = df['Barcode'].str.strip()
    return df

def parse_gps(gps_str):
    try:
        lat, lon = map(float, gps_str.split())
        return (lat, lon)
    except:
        return None

def get_address_coordinates(address):
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
    except (GeocoderTimedOut, GeocoderUnavailable):
        return None
    return None

def generate_google_maps_link(gps, expected):
    if gps and expected:
        return f"https://www.google.com/maps/dir/{gps[0]},{gps[1]}/{expected[0]},{expected[1]}"
    return None

def check_match(gps, address, threshold_km=10):
    expected = get_address_coordinates(address)
    if not gps or not expected:
        return "Mismatch", None, expected, None
    distance = geodesic(gps, expected).km
    status = "Match" if distance <= threshold_km else "Mismatch"
    gmap_link = generate_google_maps_link(gps, expected)
    return status, round(distance, 10), expected, gmap_link
