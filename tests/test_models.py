"""Tests for the ICQA parser."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

MODELS_PATH = (
    Path(__file__).resolve().parents[1] / "custom_components" / "icqa" / "models.py"
)
SPEC = importlib.util.spec_from_file_location("icqa_models", MODELS_PATH)
assert SPEC and SPEC.loader
models = importlib.util.module_from_spec(SPEC)
sys.modules["icqa_models"] = models
SPEC.loader.exec_module(models)


class ICQAModelsTest(unittest.TestCase):
    """Test ICQA model parsing."""

    def test_parse_numeric_value_accepts_decimal_comma(self) -> None:
        """Decimal comma values are parsed as floats."""
        self.assertEqual(models.parse_numeric_value("1,5"), 1.5)
        self.assertEqual(models.parse_numeric_value("42"), 42.0)
        self.assertIsNone(models.parse_numeric_value("-"))

    def test_parse_payload_uses_station_id_and_catalan_names(self) -> None:
        """The parser keeps stable station IDs and Catalan pollutant names."""
        data = models.parse_icqa_payload(
            {
                "fecha": "202606221500",
                "features": [
                    {
                        "type": "Feature",
                        "id": "ES0001A",
                        "properties": {
                            "id": "ES0001A",
                            "nom": "Barcelona (Prova)",
                            "localitat": "Barcelona",
                            "dataActualitzacio": "22/06/2026 15:00",
                            "dataInst": "01/01/1993",
                            "qualitat2021": "bona",
                            "contaminants": [
                                {
                                    "id": "10",
                                    "abbr": "PM10",
                                    "valor": "28",
                                    "um": "ug/m3",
                                    "qualitat2021": "raonablement_bona",
                                    "nom": {"ca": "Partícules PM10"},
                                }
                            ],
                            "contaminantsEstacio": [
                                {"abbr": "PM10", "nom": {"ca": "Partícules PM10"}}
                            ],
                            "zona": {"id": "1", "nom": "Àrea de Barcelona"},
                        },
                        "geometry": {
                            "coordinates": {
                                "lat": 41.0,
                                "lon": 2.0,
                                "alt": 12.0,
                            }
                        },
                    }
                ],
            }
        )

        station = data.stations["ES0001A"]
        self.assertEqual(station.id, "ES0001A")
        self.assertEqual(station.quality, "bona")
        self.assertEqual(station.zone_name, "Àrea de Barcelona")
        self.assertEqual(station.readings["PM10"].name, "Partícules PM10")
        self.assertEqual(station.readings["PM10"].unit, "µg/m³")


if __name__ == "__main__":
    unittest.main()
