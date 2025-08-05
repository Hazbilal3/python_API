import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

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
    geolocator = Nominatim(user_agent="delivery_checker_api/1.0", timeout=10)
    try:
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
    except (GeocoderTimedOut, GeocoderUnavailable):
        return None
    return None

def check_match(gps, address, threshold_km=2):
    address_coords = get_address_coordinates(address)
    if not gps or not address_coords:
        return "Mismatch", None, address_coords
    distance = geodesic(gps, address_coords).km
    return ("Match" if distance <= threshold_km else "Mismatch"), round(distance, 3), address_coords
