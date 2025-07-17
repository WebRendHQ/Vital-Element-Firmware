# mist_maker/init.py


# import RPi.GPIO as GPIO
from mock.gpio_interface import GPIO, USING_REAL_GPIO
from dataclasses import dataclass
from typing import Optional

@dataclass
class MistMakerConfig:
    pin: int
    water_level_pin: Optional[int] = None
    frequency: int = 400  # Hz
    duty_cycle: int = 50  # %

class MistMaker:
    def __init__(self, config: MistMakerConfig):
        self.config = config
        self.setup_gpio()
        self.pwm = None
        
    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.config.pin, GPIO.OUT)
        if self.config.water_level_pin:
            GPIO.setup(self.config.water_level_pin, GPIO.IN)
        self.pwm = GPIO.PWM(self.config.pin, self.config.frequency)
        
    def start(self, duty_cycle: Optional[int] = None):
        """Start the mist maker with optional duty cycle override"""
        dc = duty_cycle if duty_cycle is not None else self.config.duty_cycle
        self.pwm.start(dc)
        
    def stop(self):
        """Stop the mist maker"""
        self.pwm.stop()
        
    def set_intensity(self, duty_cycle: int):
        """Adjust the mist intensity via PWM duty cycle (0-100)"""
        self.pwm.ChangeDutyCycle(max(0, min(100, duty_cycle)))
        
    def check_water_level(self) -> bool:
        """Check if water level is sufficient"""
        if self.config.water_level_pin:
            return GPIO.input(self.config.water_level_pin)
        return True
        
    def cleanup(self):
        """Cleanup GPIO pins"""
        self.stop()
        GPIO.cleanup([self.config.pin])
        if self.config.water_level_pin:
            GPIO.cleanup([self.config.water_level_pin])