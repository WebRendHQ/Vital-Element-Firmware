# mock/mock_sensor.py
import random
import time
from typing import Optional

class MockW1ThermSensor:
    """Mock temperature sensor that simulates realistic temperature behavior"""
    
    def __init__(self, initial_temp: float = 25.0, min_temp: float = 15.0, max_temp: float = 35.0):
        self.current_temp = initial_temp
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.last_update = time.time()
        self.trend_direction = random.choice([-1, 1])  # Random initial trend
        self.trend_duration = random.uniform(30, 60)  # Seconds before trend changes
        self.trend_start = time.time()
        
    def get_temperature(self) -> float:
        """
        Simulate temperature readings with realistic variations:
        - Small random fluctuations
        - Gradual trending up or down
        - Bounded by min/max temperatures
        """
        current_time = time.time()
        time_diff = current_time - self.last_update
        
        # Check if we should change trend direction
        if current_time - self.trend_start > self.trend_duration:
            self.trend_direction *= -1  # Reverse trend
            self.trend_duration = random.uniform(30, 60)  # New random duration
            self.trend_start = current_time
        
        # Add slight random variation
        random_change = random.uniform(-0.1, 0.1)
        # Add trending change
        trend_change = self.trend_direction * 0.05 * time_diff
        
        # Update temperature
        self.current_temp += random_change + trend_change
        
        # Ensure temperature stays within bounds
        self.current_temp = max(self.min_temp, min(self.max_temp, self.current_temp))
        
        self.last_update = current_time
        return round(self.current_temp, 2)
    
    def get_sensors(self) -> list:
        """Mock the multiple sensor detection method"""
        return [self]
    
    def simulate_error(self, error_chance: float = 0.01) -> Optional[float]:
        """
        Occasionally simulate sensor reading errors
        Args:
            error_chance: Probability of error (0-1)
        Returns:
            Temperature reading or raises error
        """
        if random.random() < error_chance:
            raise RuntimeError("Mock sensor reading error")
        return self.get_temperature()