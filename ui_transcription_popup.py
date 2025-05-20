# ui_transcription_popup.py
import customtkinter as ctk
import app_config as config
import os # For os.startfile
import threading
import time  

class TranscriptionPopup(ctk.CTkToplevel):
    def __init__(self, master, total_files, output_folder_path, total_estimated_duration_seconds=0, **kwargs):
        super().__init__(master, **kwargs)

        self.output_folder_path = output_folder_path
        self.total_files = total_files
        self.files_processed = 0
        self.cancel_requested = threading.Event()
        self.total_estimated_duration_seconds = total_estimated_duration_seconds # Store for potential use

        self.title("Transcription Progress")
        width = getattr(config, "POPUP_WINDOW_WIDTH", 480) 

        height = getattr(config, "POPUP_WINDOW_HEIGHT", 320) 

        master_x = master.winfo_x()
        master_y = master.winfo_y()
        master_width = master.winfo_width()
        master_height = master.winfo_height()
        x = master_x + (master_width // 2) - (width // 2)
        y = master_y + (master_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.configure(fg_color=config.WINDOW_BG_COLOR)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close_button)

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=15, pady=15)


        self.main_frame.grid_rowconfigure(0, weight=0) # overall_status_label
        self.main_frame.grid_rowconfigure(1, weight=0) # current_action_label
        self.main_frame.grid_rowconfigure(2, weight=1, minsize=40) # detailed_progress_label (allow to expand if needed, but also minsize)
        self.main_frame.grid_rowconfigure(3, weight=0) # progress_bar
        self.main_frame.grid_rowconfigure(4, weight=0) # button_frame
        self.main_frame.grid_columnconfigure(0, weight=1)


        self.overall_status_label = ctk.CTkLabel(
            self.main_frame, text=f"Processing file 0 of {self.total_files}...",
            font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=14, weight="bold"),
            text_color=config.CHILD_TEXT_COLOR
        )
        self.overall_status_label.grid(row=0, column=0, pady=(0, 5), sticky="ew")

        self.current_action_label = ctk.CTkLabel(
            self.main_frame, text="Initializing...",
            font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=12),
            text_color=config.SUB_CHILD_TEXT_COLOR,
            wraplength=width - 40 # Keep wraplength
        )
        self.current_action_label.grid(row=1, column=0, pady=5, sticky="ew")

        # Label for detailed segment progress

        self.detailed_progress_label = ctk.CTkLabel(
            self.main_frame, text="", 
            font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=11),
            text_color=config.SUB_CHILD_TEXT_COLOR,
            wraplength=width - 40, # Wraps text
            justify="left",
            anchor="nw", 
            
        )
        # Make detailed_progress_label take up available vertical space but not push buttons
        self.detailed_progress_label.grid(row=2, column=0, pady=(0,5), sticky="nsew")


        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            orientation="horizontal",
            mode="determinate",
            progress_color=config.BUTTON_PRIMARY_COLOR
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=3, column=0, pady=(10,15), padx=10, sticky="ew") 

        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.grid(row=4, column=0, pady=(5,0), sticky="ew") 
        self.button_frame.grid_columnconfigure((0,1), weight=1)

        cancel_button_style_custom = {
            "hover_color": "red",
            "text_color": config.DEFAULT_BUTTON_STYLE.get("text_color", config.CHILD_TEXT_COLOR),
            "corner_radius": config.DEFAULT_BUTTON_STYLE.get("corner_radius", 8)
        }
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel",
            command=self.request_cancel,
            fg_color=config.ACCENT_COLOR,
            font=ctk.CTkFont(family=config.BUTTON_FONT_TUPLE[0], size=config.BUTTON_FONT_TUPLE[1], weight=config.BUTTON_FONT_TUPLE[2]),
            **cancel_button_style_custom
        )
        self.cancel_button.grid(row=0, column=0, padx=(0,5), sticky="ew")

        self.go_to_folder_button = ctk.CTkButton(
            self.button_frame, text="Go to Folder",
            command=self.open_output_folder,
            state="disabled",
            font=ctk.CTkFont(family=config.BUTTON_FONT_TUPLE[0], size=config.BUTTON_FONT_TUPLE[1], weight=config.BUTTON_FONT_TUPLE[2]),
            **config.DEFAULT_BUTTON_STYLE
        )
        self.go_to_folder_button.grid(row=0, column=1, padx=(5,0), sticky="ew")

        self.ok_button = None

    def update_overall_status(self, files_done: int):
        self.files_processed = files_done
        if self.winfo_exists():
            self.overall_status_label.configure(text=f"Processing file {files_done} of {self.total_files}...")
            self.update_idletasks()

    def update_current_action(self, action_text: str):
        if self.winfo_exists():

            max_len = 100 #  max characters for current_action_label
            if len(action_text) > max_len:
                action_text = action_text[:max_len-3] + "..."
            self.current_action_label.configure(text=action_text)
            self.update_idletasks()

    def update_detailed_progress(self, segment_text: str):
        if self.winfo_exists():
            max_words = 15  # Max words to display before truncating
            words = segment_text.split()
            if len(words) > max_words:
                display_text = " ".join(words[:max_words]) + "..."
            else:
                display_text = segment_text
            
            self.detailed_progress_label.configure(text=display_text)
            self.update_idletasks()

    def update_progress_bar_value(self, value: float):
        if self.winfo_exists():
            self.progress_bar.set(min(max(0.0, value), 1.0))
            self.update_idletasks()

    def process_complete(self, success=True):
        if self.winfo_exists():
            # Clear detailed progress, action label will show final status
            self.detailed_progress_label.configure(text="") 
            
            if success:
                self.overall_status_label.configure(text="Transcription Complete!")
                final_message = f"All files processed.\nOutput saved to: {os.path.basename(self.output_folder_path)}"
                # Check if path is too long for display
                max_path_len = 50 
                if len(self.output_folder_path) > max_path_len :
                    final_message = f"All files processed.\nOutput saved to folder:\n...{self.output_folder_path[-max_path_len:]}"

                self.current_action_label.configure(text=final_message)
                self.progress_bar.set(1)
                self.go_to_folder_button.configure(state="normal")
            else:
                self.overall_status_label.configure(text="Process Interrupted or Failed")
                if self.cancel_requested.is_set():
                    self.current_action_label.configure(text="Process was cancelled by the user.")
                else:
                    self.current_action_label.configure(text="An error occurred. Check console.")
                self.go_to_folder_button.configure(state="disabled")

            if hasattr(self, 'cancel_button') and self.cancel_button.winfo_exists():
                self.cancel_button.grid_remove()

            self.ok_button = ctk.CTkButton(
                self.button_frame, text="OK",
                command=self.destroy,
                font=ctk.CTkFont(family=config.BUTTON_FONT_TUPLE[0], size=config.BUTTON_FONT_TUPLE[1], weight=config.BUTTON_FONT_TUPLE[2]),
                **config.DEFAULT_BUTTON_STYLE
            )
            # If cancel button was removed, ok_button should span or be centered.
            # If go_to_folder is also there, it shares space.
            if self.go_to_folder_button.winfo_ismapped() and self.go_to_folder_button.cget("state") == "normal":
                self.ok_button.grid(row=0, column=0, padx=(0,5), sticky="ew") # next to go_to_folder
            else: # cancel is gone, go_to_folder is disabled or also gone
                self.ok_button.grid(row=0, column=0, columnspan=2, padx=5, sticky="ew")


    def request_cancel(self):
        if self.winfo_exists():
            self.update_current_action("Cancellation requested, finishing current step...")
            if hasattr(self, 'cancel_button') and self.cancel_button.winfo_exists():
                self.cancel_button.configure(state="disabled", text="Cancelling...")
            self.cancel_requested.set()
            print("Transcription cancel requested by user.")

    def on_close_button(self):
        # self.request_cancel() # No, this would prevent closing if process complete
        self.destroy() # Just destroy the window. The worker thread is a daemon.

    def open_output_folder(self):
        try:
            if os.path.exists(self.output_folder_path):
                os.startfile(self.output_folder_path)
            else:
                self.update_current_action(f"Error: Output folder not found:\n{self.output_folder_path}")
        except Exception as e:
            self.update_current_action(f"Error opening folder: {e}")
            print(f"Error opening folder {self.output_folder_path}: {e}")

if __name__ == '__main__':
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.geometry("300x200")

    def show_popup():
        popup = TranscriptionPopup(master=root, total_files=5, output_folder_path="C:/test_output/some_very_long_path_example_here_to_see_truncation", total_estimated_duration_seconds=300)
        
        long_text = "This is a very long segment of transcribed text from Whisper that could potentially be hundreds of characters long and cause UI layout issues if not handled properly by truncating it after a certain number of words or characters to keep the display neat and tidy."
        short_text = "This is a short segment."

        def simulate_updates():
            for i in range(1, 6):
                if not popup.winfo_exists() or popup.cancel_requested.is_set():
                    break
                popup.update_overall_status(i)
                popup.update_current_action(f"Main action for file {i} - a somewhat longer action description to test its truncation.")
                if i % 2 == 0:
                    popup.update_detailed_progress(long_text)
                else:
                    popup.update_detailed_progress(short_text + f" (File {i})")
                popup.update_progress_bar_value(i/5)
                time.sleep(2)
            if popup.winfo_exists():
                popup.process_complete(not popup.cancel_requested.is_set())



        threading.Thread(target=simulate_updates, daemon=True).start()

    test_button = ctk.CTkButton(root, text="Show Progress Popup", command=show_popup)
    test_button.pack(pady=20)
    root.mainloop()