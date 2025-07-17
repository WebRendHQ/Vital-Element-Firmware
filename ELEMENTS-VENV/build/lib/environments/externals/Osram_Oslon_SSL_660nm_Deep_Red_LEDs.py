# red_light/init.py


# import RPi.GPIO as GPIO
from mock.gpio_interface import GPIO, USING_REAL_GPIO
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RedLightConfig:
    pins: List[int]
    frequency: int = 1000  # Hz
    initial_intensity: int = 100  # %

class RedLight:
    def __init__(self, config: RedLightConfig):
        self.config = config
        self.pwm_controllers = {}
        self.setup_gpio()
        
    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        for pin in self.config.pins:
            GPIO.setup(pin, GPIO.OUT)
            self.pwm_controllers[pin] = GPIO.PWM(pin, self.config.frequency)
            
    def start(self, intensity: Optional[int] = None):
        """Start all LED arrays"""
        intensity = intensity if intensity is not None else self.config.initial_intensity
        for pwm in self.pwm_controllers.values():
            pwm.start(intensity)
            
    def stop(self):
        """Stop all LED arrays"""
        for pwm in self.pwm_controllers.values():
            pwm.stop()
            
    def set_intensity(self, intensity: int):
        """Set intensity for all LEDs (0-100)"""
        for pwm in self.pwm_controllers.values():
            pwm.ChangeDutyCycle(max(0, min(100, intensity)))
            
    def cleanup(self):
        """Cleanup GPIO pins"""
        self.stop()
        GPIO.cleanup(self.config.pins)