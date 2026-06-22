"""Data models and parsing helpers for the ICQA Catalunya API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Any, Self
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Europe/Madrid")


@dataclass(frozen=True)
class HistoricReading:
    """A historical pollutant value published by the ICQA API."""

    period: str
    value: float | None
    raw_value: str | None
    quality: str | None
    legacy_quality: str | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Self:
        """Create a historic reading from an API dictionary."""
        raw_value = _as_str_or_none(data.get("valor"))
        return cls(
            period=_as_str_or_none(data.get("data")) or "",
            value=parse_numeric_value(raw_value),
            raw_value=raw_value,
            quality=normalize_quality(data.get("qualitat2021")),
            legacy_quality=normalize_quality(data.get("qualitat")),
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "period": self.period,
            "value": self.value,
            "raw_value": self.raw_value,
            "quality": self.quality,
            "legacy_quality": self.legacy_quality,
        }


@dataclass(frozen=True)
class StationContaminant:
    """A pollutant that a station declares as measured."""

    abbr: str
    name: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Self:
        """Create a station contaminant from an API dictionary."""
        abbr = normalize_contaminant_abbr(data.get("abbr"))
        return cls(abbr=abbr, name=localized_name(data.get("nom"), abbr))

    def as_dict(self) -> dict[str, str]:
        """Return a JSON-serializable representation."""
        return {"abbr": self.abbr, "name": self.name}


@dataclass(frozen=True)
class ContaminantReading:
    """A current pollutant reading for a station."""

    id: str
    abbr: str
    name: str
    value: float | None
    raw_value: str | None
    unit: str | None
    quality: str | None
    legacy_quality: str | None
    history: tuple[HistoricReading, ...]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Self:
        """Create a contaminant reading from an API dictionary."""
        abbr = normalize_contaminant_abbr(data.get("abbr"))
        raw_value = _as_str_or_none(data.get("valor"))
        history = tuple(
            HistoricReading.from_api(item)
            for item in data.get("historic", [])
            if isinstance(item, dict)
        )
        return cls(
            id=_as_str_or_none(data.get("id")) or slugify_key(abbr),
            abbr=abbr,
            name=localized_name(data.get("nom"), abbr),
            value=parse_numeric_value(raw_value),
            raw_value=raw_value,
            unit=normalize_unit(data.get("um")),
            quality=normalize_quality(data.get("qualitat2021")),
            legacy_quality=normalize_quality(data.get("qualitat")),
            history=history,
        )

    @property
    def unique_key(self) -> str:
        """Return the stable reading key used in entity unique IDs."""
        return slugify_key(self.id or self.abbr)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "id": self.id,
            "abbr": self.abbr,
            "name": self.name,
            "value": self.value,
            "raw_value": self.raw_value,
            "unit": self.unit,
            "quality": self.quality,
            "legacy_quality": self.legacy_quality,
            "history": [item.as_dict() for item in self.history],
        }


@dataclass(frozen=True)
class Station:
    """An ICQA station."""

    id: str
    name: str
    locality: str | None
    address: str | None
    postal_code: str | None
    zone_id: str | None
    zone_name: str | None
    latitude: float | None
    longitude: float | None
    altitude: float | None
    elevation: float | None
    quality: str | None
    legacy_quality: str | None
    updated_at: datetime | None
    installed_on: date | None
    emission_source: str | None
    urbanization: str | None
    measured_contaminants: tuple[StationContaminant, ...]
    readings: dict[str, ContaminantReading]

    @classmethod
    def from_feature(cls, feature: dict[str, Any]) -> Self:
        """Create a station from a GeoJSON feature."""
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or {}
        zone = properties.get("zona") or {}

        station_id = _as_str_or_none(properties.get("id")) or _as_str_or_none(
            feature.get("id")
        )
        if station_id is None:
            raise ValueError("Station without id")

        readings = {
            reading.abbr: reading
            for reading in (
                ContaminantReading.from_api(item)
                for item in properties.get("contaminants", [])
                if isinstance(item, dict)
            )
            if reading.abbr
        }

        return cls(
            id=station_id,
            name=_as_str_or_none(properties.get("nom")) or station_id,
            locality=_as_str_or_none(properties.get("localitat")),
            address=_as_str_or_none(properties.get("direccio")),
            postal_code=_as_str_or_none(properties.get("codiPostal")),
            zone_id=_as_str_or_none(zone.get("id")),
            zone_name=_as_str_or_none(zone.get("nom")),
            latitude=parse_numeric_value(coordinates.get("lat")),
            longitude=parse_numeric_value(coordinates.get("lon")),
            altitude=parse_numeric_value(coordinates.get("alt")),
            elevation=parse_numeric_value(properties.get("elevacio")),
            quality=normalize_quality(properties.get("qualitat2021")),
            legacy_quality=normalize_quality(properties.get("qualitat")),
            updated_at=parse_datetime(properties.get("dataActualitzacio")),
            installed_on=parse_date(properties.get("dataInst")),
            emission_source=_as_str_or_none(properties.get("fontEmissio")),
            urbanization=_as_str_or_none(properties.get("grauUrbanitzacio")),
            measured_contaminants=tuple(
                StationContaminant.from_api(item)
                for item in properties.get("contaminantsEstacio", [])
                if isinstance(item, dict)
            ),
            readings=readings,
        )

    @property
    def measured_abbrs(self) -> set[str]:
        """Return the pollutant abbreviations declared by the station."""
        return {item.abbr for item in self.measured_contaminants if item.abbr}

    @property
    def sorted_readings(self) -> tuple[ContaminantReading, ...]:
        """Return readings sorted by pollutant abbreviation."""
        return tuple(sorted(self.readings.values(), key=lambda item: item.abbr))

    def station_attributes(self) -> dict[str, Any]:
        """Return station metadata suitable for entity attributes."""
        attrs: dict[str, Any] = {
            "id_estacio": self.id,
            "nom_estacio": self.name,
            "localitat": self.locality,
            "adreca": self.address,
            "codi_postal": self.postal_code,
            "zona": self.zone_name,
            "id_zona": self.zone_id,
            "latitud": self.latitude,
            "longitud": self.longitude,
            "altitud": self.altitude if self.altitude is not None else self.elevation,
            "data_actualitzacio": self.updated_at.isoformat()
            if self.updated_at
            else None,
            "data_installacio": self.installed_on.isoformat()
            if self.installed_on
            else None,
            "font_emissio": self.emission_source,
            "grau_urbanitzacio": self.urbanization,
            "contaminants_mesurats": [
                item.as_dict() for item in self.measured_contaminants
            ],
        }
        return {key: value for key, value in attrs.items() if value is not None}

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            **self.station_attributes(),
            "qualitat": self.quality,
            "qualitat_original": self.legacy_quality,
            "lectures": [reading.as_dict() for reading in self.sorted_readings],
        }


@dataclass(frozen=True)
class ICQAData:
    """Parsed ICQA API payload."""

    generated_at: datetime | None
    stations: dict[str, Station]

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Self:
        """Create parsed ICQA data from the API payload."""
        stations: dict[str, Station] = {}
        for feature in data.get("features", []):
            if not isinstance(feature, dict):
                continue
            try:
                station = Station.from_feature(feature)
            except ValueError:
                continue
            stations[station.id] = station

        return cls(
            generated_at=parse_payload_datetime(data.get("fecha")),
            stations=stations,
        )


def parse_icqa_payload(data: dict[str, Any]) -> ICQAData:
    """Parse a raw ICQA API payload."""
    return ICQAData.from_api(data)


def localized_name(value: Any, fallback: str) -> str:
    """Return the Catalan localized name from an API translation object."""
    if isinstance(value, dict):
        for key in ("ca", "oc", "es", "en"):
            localized = _as_str_or_none(value.get(key))
            if localized:
                return localized
    return fallback


def normalize_contaminant_abbr(value: Any) -> str:
    """Normalize a pollutant abbreviation."""
    text = _as_str_or_none(value)
    return text.upper() if text else ""


def normalize_quality(value: Any) -> str | None:
    """Normalize an ICQA quality value."""
    text = _as_str_or_none(value)
    return text.strip().lower() if text else None


def normalize_unit(value: Any) -> str | None:
    """Normalize units published by the API."""
    text = _as_str_or_none(value)
    if text is None:
        return None
    normalized = text.strip().replace("ug/", "µg/")
    return normalized.replace("m3", "m³")


def parse_numeric_value(value: Any) -> float | None:
    """Parse numbers that may use a Catalan decimal comma."""
    text = _as_str_or_none(value)
    if text is None or text in {"", "-"}:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def parse_payload_datetime(value: Any) -> datetime | None:
    """Parse the payload timestamp format YYYYMMDDHHMM."""
    text = _as_str_or_none(value)
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y%m%d%H%M").replace(tzinfo=LOCAL_TZ)
    except ValueError:
        return None


def parse_datetime(value: Any) -> datetime | None:
    """Parse the station update timestamp format DD/MM/YYYY HH:MM."""
    text = _as_str_or_none(value)
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y %H:%M").replace(tzinfo=LOCAL_TZ)
    except ValueError:
        return None


def parse_date(value: Any) -> date | None:
    """Parse the station installation date format DD/MM/YYYY."""
    text = _as_str_or_none(value)
    if not text:
        return None
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        return None


def slugify_key(value: str) -> str:
    """Return a stable ASCII key for an entity unique ID suffix."""
    key = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return key or "unknown"


def _as_str_or_none(value: Any) -> str | None:
    """Return a stripped string, or None for empty values."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return str(value)
