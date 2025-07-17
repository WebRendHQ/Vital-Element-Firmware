import tkinter as tk
from tkinter import ttk, messagebox
import importlib.util
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mock.mock_sensor import MockW1ThermSensor
import threading
import time

class EnvironmentRunner:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Environment Simulator")
        self.root.geometry("400x500")
        
        # Store environment file mappings
        self.env_files = {}  # Display name -> file name
        
        # Initialize mock sensor
        self.sensor = MockW1ThermSensor()
        
        # Setup UI
        self.setup_ui()
        
        # Temperature display thread
        self.temp_thread = None
        self.stop_temp_thread = False
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Instructions label
        ttk.Label(main_frame, text="Select an environment to simulate:", 
                 wraplength=350).grid(row=0, column=0, pady=10)
        
        # Environment listbox
        self.env_listbox = tk.Listbox(main_frame, width=40, height=10)
        self.env_listbox.grid(row=1, column=0, pady=10)
        
        # Buttons
        ttk.Button(main_frame, text="Run Selected Environment", 
                  command=self.run_selected_environment).grid(row=2, column=0, pady=5)
        ttk.Button(main_frame, text="Refresh Environments", 
                  command=self.load_environments).grid(row=3, column=0, pady=5)
        ttk.Button(main_frame, text="Quit", 
                  command=self.quit_application).grid(row=4, column=0, pady=5)
        
        # Temperature display
        self.temp_label = ttk.Label(main_frame, text="Current Temperature: --°C")
        self.temp_label.grid(row=5, column=0, pady=10)
        
        # Load environments initially
        self.load_environments()
        
    def format_display_name(self, filename: str) -> str:
        """Convert filename to display name"""
        # Remove .py extension
        name = filename.replace('.py', '')
        
        # Split on underscores and hyphens
        words = name.replace('_', ' ').replace('-', ' ').split()
        
        # Capitalize each word
        words = [word.capitalize() for word in words]
        
        # Join words back together
        return ' '.join(words)
        
    def load_environments(self):
        """Load available environment modules from the environments directory"""
        self.env_listbox.delete(0, tk.END)
        self.env_files.clear()
        env_path = Path(__file__).parent / 'environments'
        
        if env_path.exists():
            # Get all Python files in the environments directory
            for file in env_path.glob('*.py'):
                # Skip __init__.py and other special files
                if not file.name.startswith('__'):
                    display_name = self.format_display_name(file.name)
                    self.env_files[display_name] = file.name
                    self.env_listbox.insert(tk.END, display_name)
    
    def update_temperature(self):
        """Update temperature display in a separate thread"""
        while not self.stop_temp_thread:
            try:
                temp = self.sensor.get_temperature()
                self.temp_label.config(text=f"Current Temperature: {temp:.1f}°C")
            except Exception as e:
                print(f"Temperature reading error: {e}")
            time.sleep(1)
    
    def run_selected_environment(self):
        """Run the selected environment simulation"""
        selection = self.env_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an environment first!")
            return
        
        display_name = self.env_listbox.get(selection[0])
        filename = self.env_files[display_name]
        
        try:
            # Import the selected environment module using file path
            env_path = Path(__file__).parent / 'environments' / filename
            print(f"Loading environment from: {env_path}")
            
            if not env_path.exists():
                messagebox.showerror("Error", f"Environment file not found: {env_path}")
                return
            
            # Create module name from filename without extension
            module_name = filename.replace('.py', '')
            
            spec = importlib.util.spec_from_file_location(module_name, str(env_path))
            if spec is None:
                messagebox.showerror("Error", "Failed to create module spec")
                return
            
            module = importlib.util.module_from_spec(spec)
            if module is None:
                messagebox.showerror("Error", "Failed to create module")
                return
            
            spec.loader.exec_module(module)
            
            # Start temperature monitoring thread
            self.stop_temp_thread = False
            self.temp_thread = threading.Thread(target=self.update_temperature)
            self.temp_thread.daemon = True
            self.temp_thread.start()
            
            # Run the environment initialization in a separate thread
            if hasattr(module, 'initialize_environment'):
                print("Starting environment initialization...")
                # Modify the environment window after it's created
                def configure_env_window():
                    # Wait briefly for the window to be created
                    time.sleep(0.5)
                    for window in self.root.winfo_children():
                        if isinstance(window, tk.Toplevel):
                            # Remove window decorations
                            window.overrideredirect(True)
                            
                            # Make fullscreen - platform specific handling
                            if sys.platform.startswith('linux'):  # For Raspberry Pi and Linux
                                window.attributes('-fullscreen', True)
                            else:  # For Windows
                                window.state('zoomed')
                            
                            # Get screen dimensions
                            screen_width = window.winfo_screenwidth()
                            screen_height = window.winfo_screenheight()
                            
                            # Create a small exit button in bottom right
                            exit_button = ttk.Button(
                                window, 
                                text="×",
                                width=3,
                                command=window.destroy
                            )
                            exit_button.place(
                                x=screen_width-50, 
                                y=screen_height-50
                            )
                            
                            # Bring window to front
                            window.lift()
                            window.focus_force()
                            
                            # Bind Escape key to exit (useful for development)
                            window.bind('<Escape>', lambda e: window.destroy())
                
                env_thread = threading.Thread(
                    target=lambda: [
                        module.initialize_environment(),
                        configure_env_window()
                    ]
                )
                env_thread.daemon = True
                env_thread.start()
                
                # Keep main window responsive
                def check_env_thread():
                    if env_thread.is_alive():
                        self.root.after(100, check_env_thread)
                    
                self.root.after(100, check_env_thread)
                print("Environment initialization started")
            else:
                messagebox.showerror("Error", 
                                   f"No initialize_environment() function found in {display_name}")
                
        except Exception as e:
            print(f"Detailed error: {str(e)}")
            messagebox.showerror("Error", f"Failed to run environment: {str(e)}")
            self.stop_temp_thread = True
            if self.temp_thread:
                self.temp_thread.join()
    
    def quit_application(self):
        """Clean up and quit the application"""
        self.stop_temp_thread = True
        if self.temp_thread:
            self.temp_thread.join()
        self.root.quit()
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = EnvironmentRunner()
    app.run()
