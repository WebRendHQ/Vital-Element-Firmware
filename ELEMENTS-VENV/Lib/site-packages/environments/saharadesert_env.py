import sys
from pathlib import Path
import time
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import pygame

# Import machine controllers
from ELEMENTS_VENV.externals.TEC1_12715_Peltier_Module_with_Heatsink_and_Fan import ACUnit, ACConfig
from ELEMENTS_VENV.externals.AGPtEK_ultrasonic_mist_maker import MistMaker, MistMakerConfig
from ELEMENTS_VENV.externals.Levoit_LV600HH_Ultrasonic_Humidifier_Components import Humidifier, HumidifierConfig
from ELEMENTS_VENV.externals.Maxim_DS18B20_Programmable_Temperature_Controller import TemperatureController, TempControllerConfig
from ELEMENTS_VENV.externals.Osram_Oslon_SSL_660nm_Deep_Red_LEDs import RedLight, RedLightConfig
from ELEMENTS_VENV.externals.Sunon_HA60251V4_Industrial_Fan import Fan, FanConfig
from ELEMENTS_VENV.externals.Adafruit_MAX98357A_I2S_Digital_Audio_Amplifier import Speaker, SpeakerConfig

class SaharaEnvironment:
    def __init__(self):
        self.machines = {}
        self.video_thread = None
        self.running = False
        
    def setup_machines(self):
        """Initialize all hardware components"""
        # Setup AC Unit (Peltier)
        ac_config = ACConfig(peltier_pin=18, fan_pin=23)
        self.machines['ac'] = ACUnit(ac_config)
        
        # Setup Mist Maker
        mist_config = MistMakerConfig(pin=24)
        self.machines['mist'] = MistMaker(mist_config)
        
        # Setup Humidifier
        humid_config = HumidifierConfig(ultrasonic_pin=25)
        self.machines['humidifier'] = Humidifier(humid_config)
        
        # Setup Temperature Controller
        temp_config = TempControllerConfig(target_temp=45.0)  # Sahara-like temperature
        self.machines['temp_controller'] = TemperatureController(temp_config)
        
        # Setup Red Light (for sunset effect)
        light_config = RedLightConfig(pins=[12, 16, 20])
        self.machines['red_light'] = RedLight(light_config)
        
        # Setup Fan (for wind simulation)
        fan_config = FanConfig(pin=21)
        self.machines['fan'] = Fan(fan_config)
        
        # Setup Speaker
        speaker_config = SpeakerConfig()
        self.machines['speaker'] = Speaker(speaker_config)

    def activate_machines(self):
        """Start all machines with initial settings"""
        print("Activating Sahara Desert environment machines...")
        
        # Start AC unit at high power for initial heat
        self.machines['ac'].start(cooling_power=0, fan_speed=100)
        print("AC unit activated: Heating mode")
        
        # Start mist maker at low intensity for dust simulation
        self.machines['mist'].start(20)
        print("Mist maker activated: Light dust simulation")
        
        # Set humidifier to very low for dry conditions
        self.machines['humidifier'].start(10)
        print("Humidifier activated: Maintaining low humidity")
        
        # Start temperature monitoring
        self.machines['temp_controller'].start_monitoring()
        print("Temperature controller activated: Target 45°C")
        
        # Initialize red lights (off initially)
        self.machines['red_light'].start(0)
        print("Red lights ready for sunset simulation")
        
        # Start fan for wind simulation
        self.machines['fan'].start(50)
        print("Fan activated: Moderate wind simulation")

    def control_machines(self, video_time):
        """Control machines based on video timestamp"""
        # Example machine control timeline
        if video_time < 60:  # First minute
            self.machines['fan'].set_speed(30)  # Light breeze
            self.machines['red_light'].set_intensity(0)
            print(f"Time {video_time}s: Light desert breeze")
            
        elif 60 <= video_time < 120:  # Second minute
            self.machines['fan'].set_speed(80)  # Strong wind
            self.machines['mist'].set_intensity(40)  # More dust
            print(f"Time {video_time}s: Sandstorm simulation")
            
        elif 120 <= video_time < 180:  # Third minute
            self.machines['fan'].set_speed(50)  # Moderate wind
            self.machines['mist'].set_intensity(20)
            self.machines['red_light'].set_intensity(50)  # Sunset begins
            print(f"Time {video_time}s: Sunset beginning")
            
        elif 180 <= video_time < 240:  # Fourth minute
            self.machines['red_light'].set_intensity(100)  # Full sunset
            self.machines['fan'].set_speed(30)
            print(f"Time {video_time}s: Full sunset simulation")
            
        elif video_time >= 240:  # Final minute
            self.machines['red_light'].set_intensity(70)  # Dusk
            self.machines['fan'].set_speed(20)
            print(f"Time {video_time}s: Evening desert conditions")

    def play_video(self, video_path, video_label):
        """Play video and control machines"""
        cap = cv2.VideoCapture(video_path)
        start_time = time.time()
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert frame for tkinter
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img = ImageTk.PhotoImage(image=img)
            
            # Update video display
            video_label.configure(image=img)
            video_label.image = img
            
            # Control machines based on video time
            video_time = time.time() - start_time
            self.control_machines(video_time)
            
            # Control video playback speed
            time.sleep(1/30)  # 30 FPS
            
        cap.release()

def initialize_environment():
    """Initialize and run the Sahara desert environment"""
    # Create main window for video
    video_window = tk.Toplevel()
    video_window.title("Sahara Desert Experience")
    video_window.geometry("800x600")
    
    # Create video label
    video_label = ttk.Label(video_window)
    video_label.pack(expand=True, fill='both')
    
    # Initialize environment
    env = SaharaEnvironment()
    env.setup_machines()
    env.activate_machines()
    env.running = True
    
    # Start video playback in separate thread
    video_path = Path(__file__).parent.parent / 'media' / 'sahara.mp4'
    env.video_thread = threading.Thread(
        target=env.play_video,
        args=(str(video_path), video_label)
    )
    env.video_thread.start()
    
    # Cleanup function
    def on_closing():
        env.running = False
        if env.video_thread:
            env.video_thread.join()
        for machine in env.machines.values():
            machine.cleanup()
        video_window.destroy()
    
    video_window.protocol("WM_DELETE_WINDOW", on_closing)
