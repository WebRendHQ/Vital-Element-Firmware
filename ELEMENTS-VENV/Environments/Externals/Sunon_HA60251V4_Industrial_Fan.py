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
        self.pwm = None  # Initialize before setup_gpio
        self.setup_gpio()
        
    def setup_gpio(self):
        """Setup GPIO and initialize PWM"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.config.pin, GPIO.OUT)
            self.pwm = GPIO.PWM(self.config.pin, self.config.frequency)
            self.pwm.start(0)  # Start with 0% duty cycle
        except Exception as e:
            print(f"Error setting up fan GPIO: {e}")
            raise
        
    def start(self, speed: Optional[int] = None):
        """Start fan with optional speed override"""
        if self.pwm is None:
            raise RuntimeError("Fan PWM not properly initialized")
        try:
            speed = speed if speed is not None else self.config.initial_speed
            self.pwm.ChangeDutyCycle(max(0, min(100, speed)))  # Use ChangeDutyCycle instead of start
        except Exception as e:
            print(f"Error starting fan: {e}")
            raise
        
    def stop(self):
        """Stop the fan"""
        if self.pwm:
            try:
                self.pwm.stop()
            except Exception as e:
                print(f"Error stopping fan: {e}")
                raise
        
    def set_speed(self, speed: int):
        """Set fan speed (0-100)"""
        if self.pwm is None:
            raise RuntimeError("Fan PWM not properly initialized")
        try:
            self.pwm.ChangeDutyCycle(max(0, min(100, speed)))
        except Exception as e:
            print(f"Error setting fan speed: {e}")
            raise
        
    def cleanup(self):
        """Cleanup GPIO pins"""
        try:
            self.stop()
            GPIO.cleanup([self.config.pin])
        except Exception as e:
            print(f"Error cleaning up fan: {e}")
            raise