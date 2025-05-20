# main.py

import customtkinter as ctk
import app_config as config
from ui_manager import UIManager
from PIL import Image 
import tkinter as tk 
import os # Import os

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark") 

        self.title(config.APP_NAME)
        self.geometry(f"{config.MAIN_WINDOW_WIDTH}x{config.MAIN_WINDOW_HEIGHT}")
        self.resizable(False, False) 
        self.minsize(config.MAIN_WINDOW_WIDTH, config.MAIN_WINDOW_HEIGHT)

        self.center_window()

        # --- Set main window icon ---
        try:
            if os.path.exists(config.APP_ICON_PATH):
                if config.APP_ICON_PATH.lower().endswith(".ico") and os.name == 'nt': # For .ico on Windows
                    self.iconbitmap(config.APP_ICON_PATH)
                    print(f"Attempted to load .ico: {config.APP_ICON_PATH}")
                elif config.APP_ICON_PATH.lower().endswith((".png", ".gif")): # For PNG/GIF with PhotoImage
                    pil_app_icon_image = Image.open(config.APP_ICON_PATH)
                    if pil_app_icon_image.mode != 'RGBA' and pil_app_icon_image.mode != 'RGB':
                        pil_app_icon_image = pil_app_icon_image.convert('RGBA')
                    self.tk_app_icon = tk.PhotoImage(pil_app_icon_image) 
                    self.iconphoto(True, self.tk_app_icon)
                    print(f"Attempted to load .png/.gif with PhotoImage: {config.APP_ICON_PATH}")
                else:
                    print(f"Warning: App icon format not explicitly handled for iconphoto/iconbitmap: {config.APP_ICON_PATH}")
            else:
                print(f"Warning: App icon file not found at {config.APP_ICON_PATH}")
        except FileNotFoundError: # More specific error
            print(f"Error: App icon file not found at {config.APP_ICON_PATH}")
        except tk.TclError as e: # Catch Tcl errors which can happen with iconbitmap/iconphoto
             print(f"TclError loading app icon (path: {config.APP_ICON_PATH}): {e}")
        except Exception as e:
            print(f"General error loading main app icon (path: {config.APP_ICON_PATH}): Type: {type(e).__name__}, Message: {str(e)}")


        self.ui_manager = UIManager(self)
        self.ui_manager.show_loading_screen() 

    def center_window(self):
        self.update_idletasks() 
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1: width = config.MAIN_WINDOW_WIDTH 
        if height <= 1: height = config.MAIN_WINDOW_HEIGHT 
        
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == "__main__":
    app = App()
    app.mainloop()
