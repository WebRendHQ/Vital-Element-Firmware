# fan/init.py


# import RPi.GPIO as GPIO
from mock.gpio_interface import GPIO, USING_REAL_GPIO
from dataclasses import dataclass
from typing import Optional

@dataclass
class FanConfig:
    pin: int
    frequency: int = 25000  # Hz
    initial_speed: int = 0  # %

class Fan:
    def __init__(self, config: FanConfig):
        self.config = config
        self.setup_gpio()
        self.pwm = None
        
    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.config.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.config.pin, self.config.frequency)
        
    def start(self, speed: Optional[int] = None):
        """Start fan with optional speed override"""
        speed = speed if speed is not None else self.config.initial_speed
        self.pwm.start(speed)
        
    def stop(self):
        """Stop the fan"""
        self.pwm.stop()
        
    def set_speed(self, speed: int):
        """Set fan speed (0-100)"""
        self.pwm.ChangeDutyCycle(max(0, min(100, speed)))
        
    def cleanup(self):
        """Cleanup GPIO pins"""
        self.stop()
        GPIO.cleanup([self.config.pin])