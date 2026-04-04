from math import atan2, cos, radians, sin, sqrt


def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))


def normalize_location(location):
    if not location:
        raise ValueError("Location is required.")

    lat = location.get("lat", location.get("latitude"))
    lon = location.get("lon", location.get("lng", location.get("longitude")))

    if lat is None or lon is None:
        raise ValueError("Location must include lat and lon.")

    return {"lat": float(lat), "lon": float(lon)}


def zone_id_for_location(lat, lon, bucket_size=0.1):
    lat_bucket = round(round(lat / bucket_size) * bucket_size, 2)
    lon_bucket = round(round(lon / bucket_size) * bucket_size, 2)
    return f"{lat_bucket:.2f}:{lon_bucket:.2f}"


def haversine_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius_km * c

