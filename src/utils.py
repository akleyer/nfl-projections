"""
This module provides utility functions for the NFL projection model.

It includes functions to:

* Calculate impact percentages based on weather conditions (wind, precipitation, temperature)
* Create linear functions for various calculations
* Safely convert values to floats
* Format DVOA values
* Get normalized DVOA values
* Format normalized DVOA values
* Calculate win percentage from spread
* Calculate fantasy points for passing, rushing, receiving, and special teams

"""
from typing import Callable, Optional

def win_pct_from_spread(in_spread: float) -> float:
    """
    Calculate the implied win percentage from a point spread.
    
    Args:
        spread (float): The point spread (negative for favorite, positive for underdog)
    
    Returns:
        float: The implied win percentage
    """
    spread = -1*in_spread if in_spread < 0 else 1
    win_pct = (0.00187033*(spread**4))-(0.0613893*(spread**3))+(0.568552*(spread**2))+(1.96375*spread) + 49.9791
    if in_spread < 0:
        return win_pct
    else:
        return 100 - win_pct
def safe_float(value, default=0.0):
    """Safely convert a value to float, returning a default if conversion fails."""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except ValueError:
        return default

def get_normalized_dvoa(num, dvoa_value, linear_func):
    """Get normalized DVOA value using the provided linear function."""
    if dvoa_value == 'N/A':
        return 'N/A'
    try:
        return round(num * linear_func(float(dvoa_value)),1)
    except ValueError:
        return 'N/A'

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
