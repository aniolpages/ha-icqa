"""Tests for the ICQA parser."""

from __future__ import annotations

from datetime import UTC
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

    def test_parse_measurement_value_ignores_unavailable_sentinels(self) -> None:
        """Unavailable or negative sentinel values are not measurements."""
        self.assertIsNone(models.parse_measurement_value("-111.0", "no_disponible"))
        self.assertIsNone(models.parse_measurement_value("-1.0", "bona"))
        self.assertEqual(models.parse_measurement_value("0,2", "bona"), 0.2)

    def test_api_timestamps_use_europe_madrid_dst_rules(self) -> None:
        """API timestamps are local Europe/Madrid clock values."""
        self.assertEqual(
            models.parse_payload_datetime("202606221900"),
            models.datetime(2026, 6, 22, 17, 0, tzinfo=UTC),
        )
        self.assertEqual(
            models.parse_payload_datetime("202601221900"),
            models.datetime(2026, 1, 22, 18, 0, tzinfo=UTC),
        )
        self.assertEqual(
            models.parse_datetime("22/06/2026 19:00"),
            models.datetime(2026, 6, 22, 17, 0, tzinfo=UTC),
        )
        self.assertEqual(
            models.parse_datetime("22/01/2026 19:00"),
            models.datetime(2026, 1, 22, 18, 0, tzinfo=UTC),
        )

    def test_parse_payload_uses_station_id_and_catalan_names(self) -> None:
        """The parser keeps stable station IDs and Catalan pollutant names."""
        data = models.parse_icqa_payload(
            {
                "fecha": "202606221900",
                "features": [
                    {
                        "type": "Feature",
                        "id": "ES0001A",
                        "properties": {
                            "id": "ES0001A",
                            "nom": "Barcelona (Prova)",
                            "localitat": "Barcelona",
                            "dataActualitzacio": "22/06/2026 18:00",
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
                                    "historic": [
                                        {
                                            "data": "2026062214",
                                            "valor": "-111.0",
                                            "qualitat2021": "no_disponible",
                                            "qualitat": "no_disponible",
                                        }
                                    ],
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
        self.assertEqual(
            station.updated_at,
            models.datetime(2026, 6, 22, 16, 0, tzinfo=UTC),
        )
        self.assertEqual(
            station.station_attributes()["data_actualitzacio_local"],
            "2026-06-22T18:00:00+02:00",
        )
        self.assertEqual(
            data.generated_at,
            models.datetime(2026, 6, 22, 17, 0, tzinfo=UTC),
        )
        self.assertEqual(station.readings["PM10"].name, "Partícules PM10")
        self.assertEqual(station.readings["PM10"].unit, "µg/m³")
        self.assertIsNone(station.readings["PM10"].history[0].value)


if __name__ == "__main__":
    unittest.main()
