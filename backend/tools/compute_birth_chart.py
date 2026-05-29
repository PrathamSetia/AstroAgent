import ephem
import math
from datetime import datetime
from tools.geocode_place import geocode_place

# Planets we'll compute
PLANETS = {
    "Sun":     ephem.Sun,
    "Moon":    ephem.Moon,
    "Mercury": ephem.Mercury,
    "Venus":   ephem.Venus,
    "Mars":    ephem.Mars,
    "Jupiter": ephem.Jupiter,
    "Saturn":  ephem.Saturn,
    "Uranus":  ephem.Uranus,
    "Neptune": ephem.Neptune,
}

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def degrees_to_zodiac(degrees: float) -> dict:
    """Convert ecliptic longitude in degrees to zodiac sign + degree within sign."""
    degrees = degrees % 360
    sign_index = int(degrees // 30)
    degree_in_sign = degrees % 30
    return {
        "sign": ZODIAC_SIGNS[sign_index],
        "degree": round(degree_in_sign, 2),
        "absolute_degree": round(degrees, 2)
    }

def compute_birth_chart(
    date: str,       # "YYYY-MM-DD"
    time: str,       # "HH:MM"  (24hr, local time)
    place: str       # e.g. "Delhi, India"
) -> dict:
    """
    Compute a natal birth chart for the given date, time, and place.
    Returns planetary positions in zodiac signs.
    """

    # ── Validate inputs ───────────────────────────────────────────────────────
    if not date or not time or not place:
        return {"error": "date, time, and place are all required."}

    try:
        birth_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": f"Invalid date/time format. Use YYYY-MM-DD and HH:MM. Got: {date} {time}"}

    # Sanity check — no future birth dates
    if birth_dt > datetime.now():
        return {"error": "Birth date cannot be in the future."}

    # ── Geocode the place ─────────────────────────────────────────────────────
    geo = geocode_place(place)
    if "error" in geo:
        return {"error": f"Could not resolve birthplace: {geo['error']}"}

    # ── Set up observer ───────────────────────────────────────────────────────
    observer = ephem.Observer()
    observer.lat  = str(geo["lat"])
    observer.lon  = str(geo["lng"])
    observer.elevation = 0

    # ephem expects UTC — convert local time using timezone offset
    # For simplicity we use pytz via the timezone string
    try:
        import pytz
        tz = pytz.timezone(geo["timezone"])
        local_dt = tz.localize(birth_dt)
        utc_dt = local_dt.astimezone(pytz.utc)
        observer.date = utc_dt.strftime("%Y/%m/%d %H:%M:%S")
    except Exception:
        # Fallback: treat as UTC
        observer.date = birth_dt.strftime("%Y/%m/%d %H:%M:%S")

    # ── Compute planets ───────────────────────────────────────────────────────
    positions = {}
    for name, PlanetClass in PLANETS.items():
        try:
            planet = PlanetClass(observer)
            # Get ecliptic longitude
            ecl = ephem.Ecliptic(planet, epoch=ephem.J2000)
            lon_deg = math.degrees(float(ecl.lon))
            positions[name] = degrees_to_zodiac(lon_deg)
        except Exception as e:
            positions[name] = {"error": str(e)}

    # ── Ascendant (rising sign) ───────────────────────────────────────────────
    try:
        lst = float(observer.sidereal_time())  # in radians
        lat_rad = float(observer.lat)
        # Simplified ascendant calculation
        asc_rad = math.atan2(
            math.cos(lst),
            -(math.sin(lst) * math.cos(ephem.degrees('23:26:00')) +
              math.tan(lat_rad) * math.sin(ephem.degrees('23:26:00')))
        )
        asc_deg = math.degrees(asc_rad) % 360
        ascendant = degrees_to_zodiac(asc_deg)
    except Exception:
        ascendant = {"sign": "Unknown", "degree": 0, "absolute_degree": 0}

    return {
        "birth_date": date,
        "birth_time": time,
        "birthplace": geo["display_name"],
        "timezone": geo["timezone"],
        "ascendant": ascendant,
        "planets": positions
    }