import sys
from pathlib import Path
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from scipy.signal import savgol_filter
from dataclasses import dataclass
import json
import logging
from typing import Dict, Optional
import pygame

# Import machine components
from Environments.Externals.TEC1_12715_Peltier_Module_with_Heatsink_and_Fan import ACUnit, ACConfig
from Environments.Externals.AGPTEK_ultrasonic_mist_maker import MistMaker, MistMakerConfig
from Environments.Externals.Levoit_LV600HH_Ultrasonic_Humidifier_Components import Humidifier, HumidifierConfig
from Environments.Externals.Maxim_DS18B20_Programmable_Temperature_Controller import TemperatureController, TempControllerConfig
from Environments.Externals.Osram_Oslon_SSL_660nm_Deep_Red_LEDs import RedLight, RedLightConfig
from Environments.Externals.Sunon_HA60251V4_Industrial_Fan import Fan, FanConfig
from Environments.Externals.Adafruit_MAX98357A_I2S_Digital_Audio_Amplifier import Speaker, SpeakerConfig

class AnalyzerEnvironment:
    def __init__(self):
        self.running = True
        self.video_path = None
        self.output_path = None
        self.metrics_history = []
        self.logger = self._setup_logger()
        self.machines = {}
        pygame.mixer.init()

    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def setup_machines(self):
        """Initialize all hardware components"""
        try:
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
            temp_config = TempControllerConfig(target_temp=45.0)
            self.machines['temp_controller'] = TemperatureController(temp_config)
            
            # Setup Red Light
            light_config = RedLightConfig(pins=[12, 16, 20])
            self.machines['red_light'] = RedLight(light_config)
            
            # Setup Fan
            fan_config = FanConfig(pin=21)
            self.machines['fan'] = Fan(fan_config)
            
            # Setup Speaker
            speaker_config = SpeakerConfig()
            self.machines['speaker'] = Speaker(speaker_config)
            
            self.logger.info("All machines initialized successfully")
        except Exception as e:
            self.logger.error(f"Error setting up machines: {str(e)}")
            raise

    def control_machines(self, metrics):
        """Control machines based on analyzed metrics"""
        try:
            # Fan control based on motion/wind
            if 'fan' in self.machines:
                self.machines['fan'].set_speed(metrics['wind_speed'])
            
            # Mist maker control based on dust
            if 'mist' in self.machines:
                self.machines['mist'].set_intensity(metrics['dust_level'])
            
            # Red light control based on lighting
            if 'red_light' in self.machines:
                self.machines['red_light'].set_intensity(metrics['red_intensity'])
            
            # Temperature control
            if 'temp_controller' in self.machines:
                target_temp = 35 + (metrics['temperature_factor'] * 15)
                self.machines['temp_controller'].set_target_temperature(target_temp)
            
            # Humidifier control (inverse to temperature)
            if 'humidifier' in self.machines:
                humidity = max(10, 100 - metrics['temperature_factor'] * 90)
                self.machines['humidifier'].set_intensity(humidity)
            
        except Exception as e:
            self.logger.error(f"Error controlling machines: {str(e)}")

    def analyze_video(self, video_path: Path) -> None:
        """Analyze video and generate machine control settings"""
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError("Could not open video file")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Analysis state variables
            prev_frame = None
            motion_history = []
            
            frame_count = 0
            while self.running and frame_count < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Calculate timestamp
                timestamp = frame_count / fps
                
                # Analyze frame
                metrics = self._analyze_frame(frame, prev_frame, motion_history)
                metrics['timestamp'] = timestamp
                
                # Control machines based on analysis
                self.control_machines(metrics)
                
                # Store metrics
                self.metrics_history.append(metrics)
                
                # Update progress
                if frame_count % 30 == 0:  # Update every 30 frames
                    progress = (frame_count / total_frames) * 100
                    self.logger.info(f"Analysis Progress: {progress:.1f}%")
                
                prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame_count += 1
                
            self._generate_control_file()
            
        except Exception as e:
            self.logger.error(f"Error during video analysis: {str(e)}")
            raise
        finally:
            if 'cap' in locals():
                cap.release()

    def _analyze_frame(self, frame, prev_frame, motion_history):
        """Analyze a single frame for various metrics"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Motion Analysis
        motion_intensity = 0
        if prev_frame is not None:
            motion = cv2.absdiff(gray, prev_frame)
            motion_score = np.mean(motion) * 2
            motion_history.append(motion_score)
            
            if len(motion_history) > 30:
                motion_history.pop(0)
                smoothed_motion = savgol_filter(motion_history, 
                                             min(15, len(motion_history)), 3)
                motion_intensity = np.clip(smoothed_motion[-1] * 2, 0, 100)
        
        # Dust Analysis
        dust_level = np.clip(cv2.Laplacian(gray, cv2.CV_64F).var() / 100, 0, 100)
        
        # Light Analysis
        brightness = np.mean(gray) / 255.0
        red_intensity = np.mean(frame[:, :, 2]) / 2.55
        
        # Temperature Factor
        temp_factor = (brightness * 0.7 + red_intensity * 0.3)
        
        # Wind Speed
        wind_speed = (motion_intensity * 0.8 + dust_level * 0.2)
        
        return {
            'motion_intensity': float(motion_intensity),
            'dust_level': float(dust_level),
            'red_intensity': float(red_intensity),
            'brightness': float(brightness),
            'temperature_factor': float(temp_factor),
            'wind_speed': float(wind_speed)
        }

    def _generate_control_file(self):
        """Generate machine control settings file"""
        output_data = {
            'metadata': {
                'video_path': str(self.video_path),
                'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_frames': len(self.metrics_history)
            },
            'frame_metrics': self.metrics_history,
            'machine_controls': self._generate_machine_controls()
        }
        
        output_path = self.video_path.parent / f"{self.video_path.stem}_controls.json"
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        self.logger.info(f"Control file generated: {output_path}")

    def _generate_machine_controls(self):
        """Generate machine control settings from metrics history"""
        controls = []
        for metrics in self.metrics_history:
            control_settings = {
                'timestamp': metrics['timestamp'],
                'fan_speed': metrics['wind_speed'],
                'mist_intensity': metrics['dust_level'],
                'red_light_intensity': metrics['red_intensity'],
                'temperature': 35 + (metrics['temperature_factor'] * 15),
                'humidifier': max(10, 100 - metrics['temperature_factor'] * 90)
            }
            controls.append(control_settings)
        return controls

    def cleanup_machines(self):
        """Cleanup all machine components"""
        for machine_name, machine in self.machines.items():
            try:
                machine.cleanup()
                self.logger.info(f"Cleaned up {machine_name}")
            except Exception as e:
                self.logger.error(f"Error cleaning up {machine_name}: {str(e)}")

    def create_gui(self):
        """Create GUI for video selection and analysis"""
        self.window = tk.Tk()
        self.window.title("Environment Video Analyzer")
        self.window.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Video selection
        ttk.Label(main_frame, text="Select Video File:").pack(pady=10)
        select_btn = ttk.Button(
            main_frame, 
            text="Browse", 
            command=self._select_video
        )
        select_btn.pack(pady=5)
        
        # File path display
        self.file_label = ttk.Label(main_frame, text="No file selected")
        self.file_label.pack(pady=10)
        
        # Machine status
        machine_frame = ttk.LabelFrame(main_frame, text="Machine Status", padding="10")
        machine_frame.pack(fill=tk.X, pady=10)
        
        self.machine_labels = {}
        for machine in ['fan', 'mist', 'red_light', 'temp_controller', 'humidifier']:
            self.machine_labels[machine] = ttk.Label(machine_frame, text=f"{machine}: Not initialized")
            self.machine_labels[machine].pack(anchor=tk.W)
        
        # Control buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        self.init_btn = ttk.Button(
            btn_frame,
            text="Initialize Machines",
            command=self._initialize_machines
        )
        self.init_btn.pack(side=tk.LEFT, padx=5)
        
        self.analyze_btn = ttk.Button(
            btn_frame,
            text="Analyze and Control",
            command=self._start_analysis,
            state=tk.DISABLED
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        # Status display
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(pady=10)
        
        # Cleanup on window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.window.mainloop()

    def _select_video(self):
        """Handle video file selection"""
        file_path = filedialog.askopenfilename(
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if file_path:
            self.video_path = Path(file_path)
            self.file_label.config(text=f"Selected: {self.video_path.name}")
            if len(self.machines) > 0:  # Only enable if machines are initialized
                self.analyze_btn.config(state=tk.NORMAL)

    def _initialize_machines(self):
        """Initialize machine components"""
        try:
            self.setup_machines()
            self.init_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Machines initialized successfully")
            
            # Update machine status labels
            for machine in self.machine_labels:
                self.machine_labels[machine].config(text=f"{machine}: Ready")
                
            if self.video_path:
                self.analyze_btn.config(state=tk.NORMAL)
                
        except Exception as e:
            self.status_label.config(text=f"Error initializing machines: {str(e)}")

    def _on_closing(self):
        """Handle window closing"""
        self.running = False
        self.cleanup_machines()
        self.window.destroy()

    def _start_analysis(self):
        """Start video analysis and machine control"""
        self.analyze_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Analysis and control in progress...")
        
        def analysis_thread():
            try:
                self.analyze_video(self.video_path)
                self.window.after(0, lambda: self.status_label.config(
                    text="Analysis complete! Control file generated."
                ))
            except Exception as e:
                self.window.after(0, lambda: self.status_label.config(
                    text=f"Error: {str(e)}"
                ))
            finally:
                self.window.after(0, lambda: self.analyze_btn.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=analysis_thread)
        thread.daemon = True
        thread.start()

def initialize_environment():
    """Initialize the analyzer environment"""
    analyzer = AnalyzerEnvironment()
    analyzer.create_gui() 