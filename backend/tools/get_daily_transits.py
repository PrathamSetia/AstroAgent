import ephem
import math
from datetime import datetime
from tools.compute_birth_chart import PLANETS, degrees_to_zodiac

ASPECTS = {
    "Conjunction": 0,
    "Sextile":     60,
    "Square":      90,
    "Trine":       120,
    "Opposition":  180,
}
ORB = 6  # degrees of allowance for an aspect to count

def get_planet_longitude(planet_class, date_str: str) -> float:
    """Return ecliptic longitude in degrees for a planet on a given date."""
    obs = ephem.Observer()
    obs.date = date_str
    obs.lat = "0"
    obs.lon = "0"
    planet = planet_class(obs)
    ecl = ephem.Ecliptic(planet, epoch=ephem.J2000)
    return math.degrees(float(ecl.lon)) % 360

def find_aspects(transit_deg: float, natal_deg: float, planet_name: str, natal_planet: str) -> list:
    """Check if a transit planet forms any aspect to a natal planet."""
    found = []
    diff = abs(transit_deg - natal_deg) % 360
    if diff > 180:
        diff = 360 - diff
    for aspect_name, angle in ASPECTS.items():
        if abs(diff - angle) <= ORB:
            found.append({
                "aspect": aspect_name,
                "transit_planet": planet_name,
                "natal_planet": natal_planet,
                "orb": round(abs(diff - angle), 2)
            })
    return found

def get_daily_transits(natal_chart: dict, date: str = None) -> dict:
    """
    Compute today's planetary transits and their aspects to the natal chart.
    natal_chart: output from compute_birth_chart()
    date: "YYYY-MM-DD" — defaults to today
    """
    if not natal_chart or "planets" not in natal_chart:
        return {"error": "Valid natal chart required. Please compute birth chart first."}

    if date is None:
        date = datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")
    else:
        try:
            datetime.strptime(date, "%Y-%m-%d")
            date = date.replace("-", "/") + " 12:00:00"
        except ValueError:
            return {"error": f"Invalid date format. Use YYYY-MM-DD. Got: {date}"}

    # ── Current sky positions ─────────────────────────────────────────────────
    transit_positions = {}
    for name, PlanetClass in PLANETS.items():
        try:
            lon = get_planet_longitude(PlanetClass, date)
            transit_positions[name] = degrees_to_zodiac(lon)
        except Exception as e:
            transit_positions[name] = {"error": str(e)}

    # ── Aspects to natal chart ────────────────────────────────────────────────
    aspects_found = []
    for t_name, t_data in transit_positions.items():
        if "error" in t_data:
            continue
        for n_name, n_data in natal_chart["planets"].items():
            if "error" in n_data:
                continue
            aspects = find_aspects(
                t_data["absolute_degree"],
                n_data["absolute_degree"],
                t_name,
                n_name
            )
            aspects_found.extend(aspects)

    # Sort by orb (tightest aspects first)
    aspects_found.sort(key=lambda x: x["orb"])

    return {
        "date": date.split(" ")[0].replace("/", "-"),
        "transit_positions": transit_positions,
        "aspects_to_natal": aspects_found[:10],  # top 10 tightest
        "aspect_count": len(aspects_found)
    }