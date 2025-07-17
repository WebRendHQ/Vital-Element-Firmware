from mock.gpio_interface import GPIO
from dataclasses import dataclass
from typing import Dict, Optional, List
import time

@dataclass
class PCBConfig:
    power_pins: Dict[str, int]  # Dictionary of power rail names and their monitoring pins
    status_led_pin: Optional[int] = None
    voltage_monitoring_pins: Optional[Dict[str, int]] = None
    temperature_monitoring_pins: Optional[Dict[str, int]] = None
    
class PCBController:
    def __init__(self, config: PCBConfig):
        self.config = config
        self.setup_gpio()
        self.power_status = {}
        
    def setup_gpio(self):
        """Initialize all GPIO pins for PCB monitoring"""
        GPIO.setmode(GPIO.BCM)
        
        # Setup power monitoring pins
        for rail, pin in self.config.power_pins.items():
            GPIO.setup(pin, GPIO.IN)
            self.power_status[rail] = False
            
        # Setup status LED if configured
        if self.config.status_led_pin:
            GPIO.setup(self.config.status_led_pin, GPIO.OUT)
            
        # Setup voltage monitoring if configured
        if self.config.voltage_monitoring_pins:
            for pin in self.config.voltage_monitoring_pins.values():
                GPIO.setup(pin, GPIO.IN)
                
        # Setup temperature monitoring if configured
        if self.config.temperature_monitoring_pins:
            for pin in self.config.temperature_monitoring_pins.values():
                GPIO.setup(pin, GPIO.IN)
    
    def check_power_rails(self) -> Dict[str, bool]:
        """Check status of all power rails"""
        for rail, pin in self.config.power_pins.items():
            self.power_status[rail] = bool(GPIO.input(pin))
        return self.power_status
    
    def set_status_led(self, state: bool):
        """Control status LED if configured"""
        if self.config.status_led_pin:
            GPIO.output(self.config.status_led_pin, GPIO.HIGH if state else GPIO.LOW)
    
    def read_voltages(self) -> Optional[Dict[str, float]]:
        """Read voltage levels if monitoring is configured"""
        if not self.config.voltage_monitoring_pins:
            return None
            
        voltages = {}
        for rail, pin in self.config.voltage_monitoring_pins.items():
            # Convert ADC reading to voltage (implementation depends on specific ADC)
            raw_value = GPIO.input(pin)
            voltages[rail] = raw_value * (3.3 / 1024)  # Example conversion
        return voltages
    
    def read_temperatures(self) -> Optional[Dict[str, float]]:
        """Read temperature sensors if configured"""
        if not self.config.temperature_monitoring_pins:
            return None
            
        temperatures = {}
        for location, pin in self.config.temperature_monitoring_pins.items():
            # Convert reading to temperature (implementation depends on sensor type)
            raw_value = GPIO.input(pin)
            temperatures[location] = raw_value * 0.1  # Example conversion
        return temperatures
    
    def perform_health_check(self) -> Dict[str, any]:
        """Perform a complete health check of the PCB"""
        health_status = {
            "power_rails": self.check_power_rails(),
            "voltages": self.read_voltages(),
            "temperatures": self.read_temperatures(),
            "timestamp": time.time()
        }
        
        # Update status LED based on health check
        if self.config.status_led_pin:
            all_systems_go = all(health_status["power_rails"].values())
            self.set_status_led(all_systems_go)
            
        return health_status
    
    def cleanup(self):
        """Cleanup GPIO pins"""
        pins_to_cleanup = []
        pins_to_cleanup.extend(self.config.power_pins.values())
        
        if self.config.status_led_pin:
            pins_to_cleanup.append(self.config.status_led_pin)
            
        if self.config.voltage_monitoring_pins:
            pins_to_cleanup.extend(self.config.voltage_monitoring_pins.values())
            
        if self.config.temperature_monitoring_pins:
            pins_to_cleanup.extend(self.config.temperature_monitoring_pins.values())
            
        GPIO.cleanup(pins_to_cleanup)