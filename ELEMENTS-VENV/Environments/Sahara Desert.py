import sys
from pathlib import Path
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import pygame

# Import from the Externals folder in the same directory
from Environments.Externals.TEC1_12715_Peltier_Module_with_Heatsink_and_Fan import ACUnit, ACConfig
from Environments.Externals.AGPTEK_ultrasonic_mist_maker import MistMaker, MistMakerConfig
from Environments.Externals.Levoit_LV600HH_Ultrasonic_Humidifier_Components import Humidifier, HumidifierConfig
from Environments.Externals.Maxim_DS18B20_Programmable_Temperature_Controller import TemperatureController, TempControllerConfig
from Environments.Externals.Osram_Oslon_SSL_660nm_Deep_Red_LEDs import RedLight, RedLightConfig
from Environments.Externals.Sunon_HA60251V4_Industrial_Fan import Fan, FanConfig
from Environments.Externals.Adafruit_MAX98357A_I2S_Digital_Audio_Amplifier import Speaker, SpeakerConfig

class SaharaEnvironment:
    def __init__(self):
        self.machines = {}
        self.video_thread = None
        self.running = True
        # Initialize pygame mixer for audio
        pygame.mixer.init()
        
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
        
        try:
            # Start AC unit at high power for initial heat
            if 'ac' in self.machines:
                self.machines['ac'].start(cooling_power=0, fan_speed=100)
                print("AC unit activated: Heating mode")
            
            # Start mist maker at low intensity for dust simulation
            if 'mist' in self.machines:
                self.machines['mist'].start(20)
                print("Mist maker activated: Light dust simulation")
            
            # Set humidifier to very low for dry conditions
            if 'humidifier' in self.machines:
                self.machines['humidifier'].start(10)
                print("Humidifier activated: Maintaining low humidity")
            
            # Start temperature monitoring
            if 'temp_controller' in self.machines:
                self.machines['temp_controller'].start_monitoring()
                print("Temperature controller activated: Target 45°C")
            
            # Initialize red lights (off initially)
            if 'red_light' in self.machines:
                self.machines['red_light'].start(0)
                print("Red lights ready for sunset simulation")
            
            # Start fan for wind simulation
            if 'fan' in self.machines:
                self.machines['fan'].start(50)
                print("Fan activated: Moderate wind simulation")
            
        except Exception as e:
            print(f"Error activating machines: {e}")
            raise

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

    def play_video(self, video_label):
        """Video playback function"""
        video_path = Path(__file__).parent / 'Media' / 'MP4' / 'sahara.mp4'
        audio_path = Path(__file__).parent / 'Media' / 'MP3' / 'sahara_ambient.mp3'
        
        # Get screen dimensions
        screen_width = video_label.winfo_screenwidth()
        screen_height = video_label.winfo_screenheight()
        
        # Set warning colors and messages based on missing media
        video_missing = not video_path.exists()
        audio_missing = not audio_path.exists()
        
        if video_missing and audio_missing:
            bg_color = '#8B0000'  # Dark red
            message = "NOTICE:\n\nNo Video File Found at:\n" + str(video_path) + "\n\n" + \
                     "No Audio File Found at:\n" + str(audio_path) + "\n\n" + \
                     "Environment Simulation Still Active"
        elif video_missing:
            bg_color = '#4B0082'  # Indigo
            message = "NOTICE:\n\nNo Video File Found at:\n" + str(video_path) + \
                     "\n\nAudio Playing\nEnvironment Simulation Active"
        elif audio_missing:
            bg_color = '#2F4F4F'  # Dark slate gray
            message = "NOTICE:\n\nNo Audio File Found at:\n" + str(audio_path) + \
                     "\n\nVideo Playing\nEnvironment Simulation Active"
        else:
            bg_color = '#2c3e50'  # Original dark blue-grey
            message = "Loading Media..."
        
        # Configure default display with appropriate warning
        video_label.config(
            text=message,
            font=('Arial', 24, 'bold'),
            foreground='white',
            background=bg_color,
            width=screen_width,
            height=screen_height,
            wraplength=screen_width - 100,  # Wrap text with some margin
            justify='center',
            anchor='center',
            image=''  # Clear any existing image
        )
        video_label.pack(expand=True, fill='both')
        video_label.update()  # Force update of the label
        
        # Try to initialize audio if available
        if not audio_missing:
            try:
                pygame.mixer.init()
                pygame.mixer.music.load(str(audio_path))
                pygame.mixer.music.play(-1)
                print("Audio playback started")
            except Exception as e:
                print(f"Audio initialization failed: {e}")
                video_label.config(
                    text=video_label.cget('text') + "\n(Audio Failed to Load)",
                    background='#8B4513'  # Saddle brown for error state
                )

        # Exit if no video file
        if video_missing:
            return
        
        # Try to initialize video
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                print("Video file could not be opened")
                video_label.config(
                    text="Video Failed to Load\nEnvironment Simulation Active",
                    background='#8B4513'  # Saddle brown for error state
                )
                return
            
            print("Video playback started")
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
                    continue
                
                # Resize frame to fill screen
                frame = cv2.resize(frame, (screen_width, screen_height))
                
                # Convert and display frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image=image)
                video_label.config(image=photo)
                video_label.image = photo
                time.sleep(1/30)
                
        except Exception as e:
            print(f"Video playback error: {e}")
            video_label.config(
                text="Video Playback Error\nEnvironment Simulation Active",
                background='#8B4513'  # Saddle brown for error state
            )
        finally:
            if 'cap' in locals() and cap is not None:
                cap.release()
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except:
                pass

def initialize_environment():
    """Initialize and run the Sahara desert environment"""
    # Create a new window that stays responsive
    video_window = tk.Toplevel()
    video_window.title("Sahara Desert Experience")
    
    # Get screen dimensions
    screen_width = video_window.winfo_screenwidth()
    screen_height = video_window.winfo_screenheight()
    
    # Configure the window to be fullscreen
    video_window.attributes('-fullscreen', True)
    video_window.configure(background='black')  # Set black background
    
    # Create video label that fills the screen
    video_label = ttk.Label(video_window)
    video_label.pack(expand=True, fill='both')
    
    # Create a round exit button style
    style = ttk.Style()
    style.configure('Round.TButton', 
                   padding=0,
                   relief='flat',
                   background='#ff0000',
                   foreground='white',
                   font=('Arial', 12, 'bold'))
    
    # Create the round exit button
    exit_button = ttk.Button(
        video_window,
        text="○",  # Using circle character
        style='Round.TButton',
        width=2,
        command=lambda: on_closing()
    )
    
    # Initialize environment
    env = SaharaEnvironment()
    env.running = True
    
    def update_status(message):
        """Update status label safely from any thread"""
        if video_window.winfo_exists():  # Check if window still exists
            video_window.after(0, lambda: video_label.config(text=message))
    
    def setup_and_activate():
        """Setup and activate machines with status updates"""
        try:
            update_status("Setting up machines...")
            env.setup_machines()
            update_status("Activating machines...")
            env.activate_machines()
            update_status("Environment running")
            # Hide status label after successful setup
            video_label.pack_forget()
            print("Environment initialization completed")
        except Exception as e:
            error_msg = f"Environment setup failed: {e}"
            print(f"Error in environment setup: {e}")
            if video_window.winfo_exists():
                video_window.after(0, lambda: messagebox.showerror("Error", error_msg))
                video_window.after(0, video_window.destroy)
            env.running = False
    
    def start_video_playback():
        """Start video playback with status updates"""
        try:
            if env.running and video_window.winfo_exists():
                update_status("Starting media playback...")
                env.play_video(video_label)
        except Exception as e:
            print(f"Video playback error: {e}")
            update_status("Media playback error")
    
    def periodic_update():
        """Keep GUI responsive by processing events periodically"""
        if env.running and video_window.winfo_exists():
            try:
                video_window.update_idletasks()  # Process any pending GUI events
                # Ensure exit button stays on top
                exit_button.lift()
                video_window.after(100, periodic_update)  # Schedule next update
            except Exception as e:
                print(f"GUI update error: {e}")
    
    def on_closing():
        """Handle window closing"""
        print("Closing environment...")
        env.running = False
        
        # Stop all machines
        try:
            for machine in env.machines.values():
                try:
                    machine.cleanup()
                except Exception as e:
                    print(f"Error during machine cleanup: {e}")
        except Exception as e:
            print(f"Error during environment cleanup: {e}")
            
        if video_window.winfo_exists():
            video_window.destroy()
    
    # Position the exit button in the bottom right corner
    exit_button.place(x=screen_width-50, y=screen_height-50)
    
    # Start setup thread
    setup_thread = threading.Thread(target=setup_and_activate)
    setup_thread.daemon = True
    setup_thread.start()
    
    # Start video thread
    video_thread = threading.Thread(target=start_video_playback)
    video_thread.daemon = True
    video_thread.start()
    
    # Configure window
    video_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start periodic updates to keep GUI responsive
    periodic_update()
