# ui_manager.py

import customtkinter as ctk
from ui_loading_Screen import LoadingScreen # Assuming LoadingScreen is now a CTkFrame
from ui_home_screen import HomeScreen # Your placeholder HomeScreen
import app_config as config
import tkinter as tk # For messagebox

class UIManager:
    def __init__(self, root_app_window: ctk.CTk):
        self.root = root_app_window
        self.current_frame = None
        self.model_successfully_loaded = False # Track model loading status

    def _destroy_current_frame(self):
        """Destroys the currently displayed frame."""
        if self.current_frame is not None:
            self.current_frame.destroy()
            self.current_frame = None

    def show_loading_screen(self):
        """Displays the loading screen."""
        self._destroy_current_frame()
        self.current_frame = LoadingScreen(
            master=self.root,
            on_continue_callback=self.handle_loading_continue, # Called when "Continue" is clicked
            on_load_complete_callback=self.handle_initial_load_complete # Called when all loading tasks are done
        )
        self.current_frame.pack(expand=True, fill="both")

    def handle_initial_load_complete(self, model_load_success: bool):
        """
        Callback executed by LoadingScreen when all its loading tasks (including model) are done.
        """
        self.model_successfully_loaded = model_load_success
        # The "Continue" button on the loading screen will be enabled by the LoadingScreen itself.
        # This callback primarily informs the UIManager about the model status.
        if not model_load_success:
            
            print("UIManager: Model loading failed. User will be informed upon clicking 'Continue'.")


    def handle_loading_continue(self):
        """
        Called when the 'Continue' button on the LoadingScreen is clicked.
        This happens AFTER the LoadingScreen's internal loading (including model) is complete.
        """
        if self.model_successfully_loaded:
            self.show_home_screen()
        else:
            # Show an error message if the model didn't load
            self._destroy_current_frame() # Remove loading screen
            error_label = ctk.CTkLabel(
                self.root,
                text="Critical Error: Transcription model failed to load.\n"
                     "CUDA might not be available or the model files are missing.\n"
                     "Please check the console output for details.\nApplication cannot continue.",
                font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=16),
                text_color="red",
                wraplength=config.MAIN_WINDOW_WIDTH - 100
            )
            error_label.pack(pady=50, padx=20, expand=True)
            
            print("UIManager: Critical error displayed due to model load failure.")


    def show_home_screen(self):
        """Displays the main home screen."""
        self._destroy_current_frame()
        if not self.model_successfully_loaded:
            print("Error: Cannot show home screen because the model did not load successfully.")

            return

        self.current_frame = HomeScreen(master=self.root)
        self.current_frame.pack(expand=True, fill="both")
        print("UIManager: Switched to Home Screen.")

