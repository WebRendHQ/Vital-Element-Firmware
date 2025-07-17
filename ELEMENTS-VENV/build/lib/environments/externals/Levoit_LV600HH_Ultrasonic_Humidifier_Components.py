# humidifier/init.py


# import RPi.GPIO as GPIO
from mock.gpio_interface import GPIO, USING_REAL_GPIO
from dataclasses import dataclass
from typing import Optional
import threading
import time

@dataclass
class HumidifierConfig:
    ultrasonic_pin: int
    water_level_pin: Optional[int] = None
    humidity_sensor_pin: Optional[int] = None
    target_humidity: float = 45.0  # %
    tolerance: float = 5.0  # %
    frequency: int = 400  # Hz for ultrasonic transducer

class Humidifier:
    def __init__(self, config: HumidifierConfig):
        self.config = config
        self.pwm = None
        self.running = False
        self.monitor_thread = None
        self.setup_gpio()
        
    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        # Setup ultrasonic transducer control
        GPIO.setup(self.config.ultrasonic_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.config.ultrasonic_pin, self.config.frequency)
        
        # Setup water level sensor if configured
        if self.config.water_level_pin:
            GPIO.setup(self.config.water_level_pin, GPIO.IN)
            
        # Setup humidity sensor if configured
        if self.config.humidity_sensor_pin:
            GPIO.setup(self.config.humidity_sensor_pin, GPIO.IN)
            
    def start(self, output_level: int = 100):
        """Start humidifier with specified output level"""
        if self.check_water_level():
            self.running = True
            self.pwm.start(output_level)
            if self.config.humidity_sensor_pin:
                self.start_monitoring()
                
    def stop(self):
        """Stop humidifier"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.pwm.stop()
        
    def set_output(self, level: int):
        """Set humidity output level (0-100)"""
        if self.check_water_level():
            self.pwm.ChangeDutyCycle(max(0, min(100, level)))
            
    def check_water_level(self) -> bool:
        """Check if water level is sufficient"""
        if self.config.water_level_pin:
            return GPIO.input(self.config.water_level_pin)
        return True
        
    def get_humidity(self) -> Optional[float]:
        """Get current humidity reading if sensor is configured"""
        if self.config.humidity_sensor_pin:
            # Implementation depends on the specific humidity sensor used
            # This is a simplified example
            return float(GPIO.input(self.config.humidity_sensor_pin))
        return None
        
    def start_monitoring(self):
        """Start humidity monitoring thread"""
        if self.config.humidity_sensor_pin:
            self.monitor_thread = threading.Thread(target=self._monitor_humidity)
            self.monitor_thread.start()
            
    def _monitor_humidity(self):
        """Monitor and adjust humidity levels"""
        while self.running:
            current_humidity = self.get_humidity()
            if current_humidity is not None:
                if current_humidity < self.config.target_humidity - self.config.tolerance:
                    self.set_output(100)
                elif current_humidity > self.config.target_humidity + self.config.tolerance:
                    self.set_output(0)
            time.sleep(5)  # Check every 5 seconds
            
    def cleanup(self):
        """Cleanup GPIO pins"""
        self.stop()
        GPIO.cleanup([self.config.ultrasonic_pin])
        if self.config.water_level_pin:
            GPIO.cleanup([self.config.water_level_pin])
        if self.config.humidity_sensor_pin:
            GPIO.cleanup([self.config.humidity_sensor_pin])