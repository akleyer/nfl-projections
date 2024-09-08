class WeatherConditions:
    temperature: float
    wind_speed: float
    precipitation_chance: float

    def __init__(self, temp, wind, precip):
        self.temperature = temp
        self.wind_speed = wind
        self.precipitation_chance = precip

    def calculate_passing_impact(self) -> float:
        return 0.999 + (0.00317 * self.wind_speed) + (-1 * (0.000458 * (self.wind_speed ** 2)))

    def calculate_precipitation_impact(self) -> float:
        return 0.015 * self.precipitation_chance

    def calculate_temperature_impact(self, base_temperature: float) -> float:
        temperature_delta = abs(base_temperature - self.temperature)
        return 1 - (0.000664 + (0.00148 * temperature_delta) + (0.0000375 * (temperature_delta ** 2)))
