# ac_unit/init.py


# import RPi.GPIO as GPIO
from mock.gpio_interface import GPIO, USING_REAL_GPIO
from dataclasses import dataclass
from typing import Optional

@dataclass
class ACConfig:
    peltier_pin: int
    fan_pin: int
    heatsink_temp_pin: Optional[int] = None
    peltier_frequency: int = 1000  # Hz
    fan_frequency: int = 25000  # Hz
    max_heatsink_temp: float = 60.0  # °C

class ACUnit:
    def __init__(self, config: ACConfig):
        self.config = config
        self.peltier_pwm = None
        self.fan_pwm = None
        self.setup_gpio()
        
    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        # Setup Peltier control
        GPIO.setup(self.config.peltier_pin, GPIO.OUT)
        self.peltier_pwm = GPIO.PWM(self.config.peltier_pin, self.config.peltier_frequency)
        self.peltier_pwm.start(0)  # Start with 0% duty cycle
        
        # Setup fan control
        GPIO.setup(self.config.fan_pin, GPIO.OUT)
        self.fan_pwm = GPIO.PWM(self.config.fan_pin, self.config.fan_frequency)
        self.fan_pwm.start(0)  # Start with 0% duty cycle
        
        # Setup heatsink temperature monitoring if configured
        if self.config.heatsink_temp_pin:
            GPIO.setup(self.config.heatsink_temp_pin, GPIO.IN)
            
    def start(self, cooling_power: int = 100, fan_speed: int = 100):
        """Start the AC unit with specified cooling power and fan speed"""
        if self.is_heatsink_safe():
            if self.peltier_pwm and self.fan_pwm:  # Check if PWM objects exist
                self.peltier_pwm.ChangeDutyCycle(cooling_power)
                self.fan_pwm.ChangeDutyCycle(fan_speed)
            else:
                raise RuntimeError("PWM objects not properly initialized")
            
    def stop(self):
        """Stop both Peltier and fan"""
        self.peltier_pwm.stop()
        self.fan_pwm.stop()
        
    def set_cooling_power(self, power: int):
        """Set Peltier cooling power (0-100)"""
        if self.is_heatsink_safe():
            self.peltier_pwm.ChangeDutyCycle(max(0, min(100, power)))
            
    def set_fan_speed(self, speed: int):
        """Set fan speed (0-100)"""
        self.fan_pwm.ChangeDutyCycle(max(0, min(100, speed)))
        
    def is_heatsink_safe(self) -> bool:
        """Check if heatsink temperature is within safe range"""
        if self.config.heatsink_temp_pin:
            # Implementation depends on the specific temperature sensor used
            # This is a simplified example
            return GPIO.input(self.config.heatsink_temp_pin) == GPIO.LOW
        return True
        
    def cleanup(self):
        """Cleanup GPIO pins"""
        self.stop()
        GPIO.cleanup([self.config.peltier_pin, self.config.fan_pin])
        if self.config.heatsink_temp_pin:
            GPIO.cleanup([self.config.heatsink_temp_pin])