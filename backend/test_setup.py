import ephem
from geopy.geocoders import Nominatim
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import math

load_dotenv()

# Test 1: ephem
observer = ephem.Observer()
observer.lat = '28.6139'
observer.lon = '77.2090'
observer.date = '2000/1/1 12:00:00'
sun = ephem.Sun(observer)
sun_deg = math.degrees(float(sun.ra))
print(f"✓ ephem works — Sun RA at J2000: {sun_deg:.4f}°")

# Test 2: geocoding
geo = Nominatim(user_agent="astroagent-test")
loc = geo.geocode("Delhi, India")
print(f"✓ geopy works — Delhi: {loc.latitude:.4f}, {loc.longitude:.4f}")

# Test 3: LLM
key = os.getenv("GROQ_API_KEY")
if not key:
    print("✗ No GROQ_API_KEY found in .env — add it before continuing")
else:
    llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=key)
    resp = llm.invoke("Say 'setup works' and nothing else.")
    print(f"✓ Groq works — {resp.content}")