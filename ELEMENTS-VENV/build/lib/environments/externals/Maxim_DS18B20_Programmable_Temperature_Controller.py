# externals/Maxim-DS18B20-Programmable-Temperature-Controller-(Heating-&-Cooling)/init.py

import time
import sys
import platform
from dataclasses import dataclass
from typing import Optional, Callable
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

@dataclass
class TempControllerConfig:
    target_temp: float = 25.0  # °C
    tolerance: float = 0.5  # °C
    reading_interval: float = 1.0  # seconds
    callback: Optional[Callable[[float], None]] = None

class TemperatureController:
    def __init__(self, config: TempControllerConfig):
        self.config = config
        self.last_reading = None
        self.running = False
        
        # Determine platform and import appropriate sensor
        if platform.system() == 'Linux' and platform.machine().startswith('arm'):
            try:
                from w1thermsensor import W1ThermSensor
                self.sensor = W1ThermSensor()
                self.using_real_sensor = True
                print("Using real W1ThermSensor")
            except (ImportError, ModuleNotFoundError) as e:
                print(f"Failed to import W1ThermSensor: {e}")
                from mock.mock_sensor import MockW1ThermSensor
                self.sensor = MockW1ThermSensor()
                self.using_real_sensor = False
                print("Falling back to mock sensor")
        else:
            from mock.mock_sensor import MockW1ThermSensor
            self.sensor = MockW1ThermSensor()
            self.using_real_sensor = False
            print("Using mock temperature sensor for development")
        
    def start_monitoring(self):
        """Start continuous temperature monitoring"""
        self.running = True
        while self.running:
            self.last_reading = self.get_temperature()
            if self.config.callback:
                self.config.callback(self.last_reading)
            time.sleep(self.config.reading_interval)
            
    def stop_monitoring(self):
        """Stop temperature monitoring"""
        self.running = False
        
    def get_temperature(self) -> float:
        """Get current temperature reading"""
        return self.sensor.get_temperature()
        
    def is_within_target(self) -> bool:
        """Check if current temperature is within target range"""
        if self.last_reading is None:
            self.last_reading = self.get_temperature()
        return abs(self.last_reading - self.config.target_temp) <= self.config.tolerance

if __name__ == "__main__":
    def temp_callback(temp):
        print(f"Current temperature: {temp}°C")
        
    config = TempControllerConfig(
        target_temp=24.0,
        callback=temp_callback
    )
    
    controller = TemperatureController(config)
    controller.start_monitoring()