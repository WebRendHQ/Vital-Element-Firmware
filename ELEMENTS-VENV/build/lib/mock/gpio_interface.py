import sys
import threading
from typing import Optional, List, Union

class MockGPIO:
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    LOW = 0
    HIGH = 1
    
    def __init__(self):
        self.pins = {}
        self.mode = None
        self.pwm_instances = {}
        
    def setmode(self, mode):
        self.mode = mode
        
    def setup(self, pin: Union[int, List[int]], direction):
        if isinstance(pin, list):
            for p in pin:
                self.pins[p] = 0
        else:
            self.pins[pin] = 0
        
    def output(self, pin: Union[int, List[int]], value):
        if isinstance(pin, list):
            for p in pin:
                self.pins[p] = value
        else:
            self.pins[pin] = value
        
    def input(self, pin):
        return self.pins.get(pin, 0)
        
    def cleanup(self, pins=None):
        if pins is None:
            self.pins.clear()
        else:
            if isinstance(pins, list):
                for pin in pins:
                    self.pins.pop(pin, None)
            else:
                self.pins.pop(pins, None)
                
    def PWM(self, pin, frequency):
        if pin not in self.pwm_instances:
            self.pwm_instances[pin] = MockPWM(pin, frequency)
        return self.pwm_instances[pin]

class MockPWM:
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle = 0
        self.running = False
        
    def start(self, duty_cycle):
        self.duty_cycle = duty_cycle
        self.running = True
        print(f"PWM started on pin {self.pin} with duty cycle {self.duty_cycle}")
        
    def stop(self):
        self.running = False
        print(f"PWM stopped on pin {self.pin}")
        
    def ChangeDutyCycle(self, duty_cycle):
        self.duty_cycle = duty_cycle
        print(f"Changed duty cycle on pin {self.pin} to {self.duty_cycle}")
        
    def ChangeFrequency(self, frequency):
        self.frequency = frequency
        print(f"Changed frequency on pin {self.pin} to {self.frequency}")

# Try to import real GPIO, fall back to mock if not available
try:
    import RPi.GPIO as GPIO
    USING_REAL_GPIO = True
    print("Using real Raspberry Pi GPIO")
except ImportError:
    GPIO = MockGPIO()
    USING_REAL_GPIO = False
    print("Using mock GPIO for development")