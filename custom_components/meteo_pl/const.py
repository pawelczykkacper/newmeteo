from datetime import timedelta

DOMAIN = "meteo_pl"
CONF_LOCATION = "location"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

API_BASE = "https://devmgramapi.meteo.pl"
GEOCODING_URL = "https://photon.dev.meteo.pl/api/"
MODEL = "um4_60"
UPDATE_INTERVAL = timedelta(hours=1)

PLATFORMS = ["sensor"]
