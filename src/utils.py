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
from typing import Callable

def safe_float(value, default=0.0):
    """Safely convert a value to float, returning a default if conversion fails."""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except ValueError:
        return default

def create_linear_function(x1: float, y1: float, x2: float, y2: float) -> Callable[[float], float]:
    """
    Create a linear function given two points on the line.
    """
    slope = (y2 - y1) / (x2 - x1)
    return lambda x: slope * x + (y1 - slope * x1)
