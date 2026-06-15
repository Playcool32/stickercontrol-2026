"""
Utilidades de geolocalizacion aproximada para "Usuarios cerca".

No se guarda direccion exacta: las coordenadas se redondean a 2 decimales
(~1.1 km de resolucion) antes de persistirse.
"""

import math

EARTH_RADIUS_KM = 6371.0


def round_coord(value: float) -> float:
    return round(value, 2)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))
