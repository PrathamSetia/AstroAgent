from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from dotenv import load_dotenv

load_dotenv()

def geocode_place(place_name: str) -> dict:
    """
    Convert a place name to latitude, longitude, and timezone.
    Returns a dict with lat, lng, timezone, and display_name.
    """
    if not place_name or not place_name.strip():
        return {"error": "Place name cannot be empty."}

    try:
        geo = Nominatim(user_agent="astroagent-v1")
        location = geo.geocode(place_name, timeout=10)

        if not location:
            return {"error": f"Could not find location: '{place_name}'. Try a more specific name."}

        tf = TimezoneFinder()
        timezone = tf.timezone_at(lat=location.latitude, lng=location.longitude)

        if not timezone:
            timezone = "UTC"

        return {
            "place": place_name,
            "display_name": location.address,
            "lat": round(location.latitude, 6),
            "lng": round(location.longitude, 6),
            "timezone": timezone
        }

    except Exception as e:
        return {"error": f"Geocoding failed: {str(e)}"}