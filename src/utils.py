from typing import Callable, Optional

def get_passing_impact_from_wind(wind_speed: Optional[float]) -> float:
    """
    Calculate a percentage modifier based on wind speed for passing plays
    """
    if wind_speed is None:
        return 1.0 
    return 0.999 + (0.00317 * wind_speed) + (-1 * (0.000458 * (wind_speed ** 2)))

def get_impact_from_precipitation(precipitation_chance: Optional[float]) -> float:
    """
    Calculate a percentage modifier based on precipitation.
    """
    if precipitation_chance is None:
        return 0.0
    return 0.0025 * precipitation_chance

def get_impact_from_temperature_delta(temperature_delta: float) -> float:
    """
    Calculate a percentage modifier based on temperature change.
    """
    return 1 - (0.000664 + (0.00148 * temperature_delta) + (0.0000375 * (temperature_delta ** 2)))

def create_linear_function(x1: float, y1: float, x2: float, y2: float) -> Callable[[float], float]:
    """
    Create a linear function given two points on the line.
    """
    slope = (y2 - y1) / (x2 - x1)
    return lambda x: slope * x + (y1 - slope * x1)