from typing import Callable, Optional

def get_pct_from_wind(wind: Optional[float]) -> float:
    """
    Calculate a percentage modifier based on wind speed.

    Args:
        wind (Optional[float]): Wind speed in mph.

    Returns:
        float: A percentage modifier based on the wind speed.
    """
    if wind is None:
        return 1  # No wind effect if wind speed is not provided
    return 0.999 + (0.00317 * wind) + (-1 * (0.000458 * (wind ** 2)))


def get_pct_from_precip(precip: Optional[float]) -> float:
    """
    Calculate a percentage modifier based on precipitation.

    Args:
        precip (Optional[float]): Precipitation level in percentage chance of rain.

    Returns:
        float: A percentage modifier based on the precipitation level.
    """
    if precip is None:
        return 0.0
    return 0.0025 * precip

def get_pct_from_temp_delta(delta: float) -> float:
    """
    Calculate a percentage modifier based on temperature change.

    Args:
        delta (float): Temperature change in degrees.

    Returns:
        float: A percentage modifier based on the temperature change.
    """
    return 1 - (0.000664 + (0.00148 * delta) + (0.0000375 * (delta ** 2)))

def linear_function(x1: float, y1: float, x2: float, y2: float) -> Callable[[float], float]:
    """
    Create a linear function given two points on the line.

    Args:
        x1 (float): x-coordinate of the first point.
        y1 (float): y-coordinate of the first point.
        x2 (float): x-coordinate of the second point.
        y2 (float): y-coordinate of the second point.

    Returns:
        Callable[[float], float]: A lambda function representing the linear equation.
    """
    m = (y2 - y1) / (x2 - x1)
    return lambda x: m * x + (y1 - m * x1)