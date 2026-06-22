"""Constants for the ICQA Catalunya integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "icqa"
NAME: Final = "ICQA Catalunya"

ICQA_API_URL: Final = "https://www.gencat.cat/territori/quaire/json/estatICQA_.json"
ICQA_INFO_URL: Final = (
    "https://mediambient.gencat.cat/ca/05_ambits_dactuacio/atmosfera/"
    "qualitat_de_laire/vols-saber-que-respires/"
)

CONF_STATION_ID: Final = "station_id"

SCAN_INTERVAL: Final = timedelta(minutes=30)
REQUEST_TIMEOUT: Final = 20

ATTR_ADDRESS: Final = "adreca"
ATTR_ALTITUDE: Final = "altitud"
ATTR_CONTAMINANTS: Final = "contaminants_mesurats"
ATTR_EMISSION_SOURCE: Final = "font_emissio"
ATTR_INSTALLATION_DATE: Final = "data_installacio"
ATTR_LATITUDE: Final = "latitud"
ATTR_LEGACY_QUALITY: Final = "qualitat_original"
ATTR_LOCALITY: Final = "localitat"
ATTR_LONGITUDE: Final = "longitud"
ATTR_STATION_ID: Final = "id_estacio"
ATTR_STATION_NAME: Final = "nom_estacio"
ATTR_UPDATED_AT: Final = "data_actualitzacio"
ATTR_URBANIZATION: Final = "grau_urbanitzacio"
ATTR_ZONE: Final = "zona"
ATTR_ZONE_ID: Final = "id_zona"

QUALITY_OPTIONS: Final = [
    "bona",
    "raonablement_bona",
    "regular",
    "pobre",
    "desfavorable",
    "molt_desfavorable",
    "extremadament_desfavorable",
    "no_disponible",
    "no_mesura",
]

NO_MEASUREMENT_STATES: Final = {"no_mesura", "no_disponible"}

MANUFACTURER: Final = "Generalitat de Catalunya"
MODEL: Final = "Estació de la XVPCA"
