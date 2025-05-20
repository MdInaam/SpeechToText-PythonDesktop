import customtkinter as ctk
import webbrowser
import threading
import app_config as config
import transcription_handler
import system_checker # For system compatibility checks

# Define a warning color 
WARNING_TEXT_COLOR = "#FFA500" # Orange
SUCCESS_TEXT_COLOR = "#00C957" # Bright Green
FAILURE_TEXT_COLOR = "#FF0000" # Red

class LoadingScreen(ctk.CTkFrame):
    def __init__(self, master, on_continue_callback=None, on_load_complete_callback=None, **kwargs):
        super().__init__(master, fg_color=config.WINDOW_BG_COLOR, **kwargs)

        self.on_continue_callback = on_continue_callback
        self.on_load_complete_callback = on_load_complete_callback

        self.model_loaded_event = threading.Event()
        self.model_load_success = False
        self.system_checks_passed_critically = False # For overall system readiness

        # --- Main container frame using grid ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(expand=True, fill="both", padx=20, pady=10)

        # Configure rows in main_container
        self.main_container.grid_rowconfigure(0, weight=0)  # Title
        self.main_container.grid_rowconfigure(1, weight=1)  # Middle content (libs and sys check)
        self.main_container.grid_rowconfigure(2, weight=0)  # Progress bar area
        self.main_container.grid_rowconfigure(3, weight=0)  # Status label area
        self.main_container.grid_rowconfigure(4, weight=0)  # Continue button area
        self.main_container.grid_columnconfigure(0, weight=1)

        # --- TOP SECTION (Row 0) ---
        self.title_label = ctk.CTkLabel(
            self.main_container,
            text=config.APP_NAME,
            font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=config.HEADING_FONT_TUPLE[1], weight=config.HEADING_FONT_TUPLE[2]),
            text_color=config.HEADING_TEXT_COLOR
        )
        self.title_label.grid(row=0, column=0, pady=(20, 15), sticky="ew")

        # --- MIDDLE SECTION (Row 1) ---
        self.info_boxes_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.info_boxes_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 20))
        self.info_boxes_frame.grid_columnconfigure(0, weight=1) # Libraries column
        self.info_boxes_frame.grid_columnconfigure(1, weight=1) # System Check column
        self.info_boxes_frame.grid_rowconfigure(0, weight=1)    # Allow frames within to expand vertically if needed

        # Libraries Box (Column 0 of info_boxes_frame)
        self.libs_info_frame = ctk.CTkFrame(self.info_boxes_frame, fg_color=config.WINDOW_SEC_BG_COLOR, corner_radius=config.SCROLLABLE_FRAME_STYLE.get("corner_radius", 6))
        self.libs_info_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0,10))
        self.libs_info_frame.grid_columnconfigure(0, weight=1) # Make content inside expand

        libs_heading_label = ctk.CTkLabel(
            self.libs_info_frame, text="Libraries/Modules Used:",
            font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=config.SUB_HEADING_FONT_TUPLE[1], weight=config.SUB_HEADING_FONT_TUPLE[2]),
            text_color=config.HEADING_TEXT_COLOR, anchor="w"
        )
        libs_heading_label.pack(fill="x", padx=10, pady=(10, 5))

        for lib_name, lib_url, name_font_config, link_font_config in config.LIBRARIES_USED:
            entry_frame = ctk.CTkFrame(self.libs_info_frame, fg_color="transparent")
            entry_frame.pack(fill="x", padx=10, pady=(0,0)) # Reduced pady
            lib_name_label = ctk.CTkLabel(entry_frame, text=lib_name, font=ctk.CTkFont(family=name_font_config[0], size=name_font_config[1], weight=name_font_config[2]), text_color=config.CHILD_TEXT_COLOR, anchor="w")
            lib_name_label.pack(fill="x", pady=(1,0))
            lib_link_label = ctk.CTkLabel(entry_frame, text=lib_url, font=ctk.CTkFont(family=link_font_config[0], size=link_font_config[1]), text_color=config.SUB_CHILD_TEXT_COLOR, cursor="hand2", anchor="w")
            lib_link_label.pack(fill="x", pady=(0,3))
            lib_link_label.bind("<Button-1>", lambda e, url=lib_url: self.open_link(url))
            lib_link_label.bind("<Enter>", lambda e, label=lib_link_label, lc=link_font_config: label.configure(font=ctk.CTkFont(family=lc[0], size=lc[1], underline=True)))
            lib_link_label.bind("<Leave>", lambda e, label=lib_link_label, lc=link_font_config: label.configure(font=ctk.CTkFont(family=lc[0], size=lc[1], underline=False)))

        # System Check Box (Column 1 of info_boxes_frame)
        self.sys_check_info_frame = ctk.CTkFrame(self.info_boxes_frame, fg_color=config.WINDOW_SEC_BG_COLOR, corner_radius=config.SCROLLABLE_FRAME_STYLE.get("corner_radius", 6))
        self.sys_check_info_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0,10))
        self.sys_check_info_frame.grid_columnconfigure(0, weight=1)

        sys_check_heading_label = ctk.CTkLabel(
            self.sys_check_info_frame, text="System Pre-requisites:",
            font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=config.SUB_HEADING_FONT_TUPLE[1], weight=config.SUB_HEADING_FONT_TUPLE[2]),
            text_color=config.HEADING_TEXT_COLOR, anchor="w"
        )
        sys_check_heading_label.pack(fill="x", padx=10, pady=(10, 5))
        
        # Placeholder labels for system checks - will be updated
        self.cuda_status_label = self._create_sys_check_label(self.sys_check_info_frame, "CUDA GPU:")
        self.ffmpeg_status_label = self._create_sys_check_label(self.sys_check_info_frame, "FFmpeg/FFprobe:")
        self.model_status_label = self._create_sys_check_label(self.sys_check_info_frame, f"Whisper Model ('{config.DEFAULT_WHISPER_MODEL}'):")
        self.summary_status_label = ctk.CTkLabel(
            self.sys_check_info_frame, text="Checking system...",
            font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=11),
            text_color=config.CHILD_TEXT_COLOR, anchor="w", justify="left", wraplength=self.sys_check_info_frame.cget("width") - 20
        )
        self.summary_status_label.pack(fill="x", padx=10, pady=(10,5))


        # --- BOTTOM ELEMENTS ---
        self.progress_bar = ctk.CTkProgressBar(self.main_container, orientation="horizontal", mode="determinate", progress_color=config.BUTTON_PRIMARY_COLOR)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, pady=(5,5), padx=50, sticky="ew")

        self.loading_status_label = ctk.CTkLabel(self.main_container, text="Initializing...", font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=12), text_color=config.SUB_CHILD_TEXT_COLOR)
        self.loading_status_label.grid(row=3, column=0, pady=(0,10), sticky="ew")

        self.continue_button = ctk.CTkButton(
            self.main_container, text="Continue",
            font=ctk.CTkFont(family=config.BUTTON_FONT_TUPLE[0], size=config.BUTTON_FONT_TUPLE[1], weight=config.BUTTON_FONT_TUPLE[2]),
            fg_color=config.BUTTON_PRIMARY_COLOR, hover_color=config.BUTTON_HOVER_COLOR, text_color=config.CHILD_TEXT_COLOR,
            corner_radius=config.DEFAULT_BUTTON_STYLE.get("corner_radius", 8), state="disabled", command=self.handle_continue
        )
        self.continue_button.grid(row=4, column=0, pady=(5, 15), sticky="s")


        self.current_progress = 0
        self.loading_steps = [
            ("Performing system checks...", 0.05, self.run_system_checks),
            ("Loading UI components...", 0.15, None), # Adjusted progress
            ("Initializing transcription engine...", 0.25, self.load_whisper_model_threaded),
            ("Finalizing setup...", 0.9, None), # Whisper load takes most time
            ("Ready!", 1.0, None)
        ]
        self.current_step_index = 0
        self.process_loading_steps()

    def _create_sys_check_label(self, master, text_prefix):
        """Helper to create a status label for system checks."""
        label = ctk.CTkLabel(
            master, text=f"{text_prefix} Checking...",
            font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=12),
            text_color=config.CHILD_TEXT_COLOR, anchor="w"
        )
        label.pack(fill="x", padx=10, pady=1)
        return label

    def run_system_checks(self):
        """Runs system checks and updates the UI."""
        report = system_checker.get_system_summary()
        all_critical_ok = True
        summary_messages = []

        # 1. PyTorch & CUDA
        pytorch_info = report['pytorch']
        if pytorch_info.get('installed') and pytorch_info.get('cuda_available'):
            gpu_name = pytorch_info['gpus'][0]['name'] if pytorch_info.get('gpus') else "Unknown GPU"
            self.cuda_status_label.configure(text=f"CUDA GPU: Detected ({gpu_name})", text_color=SUCCESS_TEXT_COLOR)
            summary_messages.append("✓ CUDA GPU ready.")
        elif pytorch_info.get('installed'):
            self.cuda_status_label.configure(text="CUDA GPU: PyTorch CPU-only or CUDA error!", text_color=FAILURE_TEXT_COLOR)
            summary_messages.append("✗ CRITICAL: PyTorch found but CUDA is not available. GPU acceleration will not work.")
            all_critical_ok = False
        else:
            self.cuda_status_label.configure(text=f"CUDA GPU: PyTorch NOT installed!", text_color=FAILURE_TEXT_COLOR)
            summary_messages.append("✗ CRITICAL: PyTorch is not installed.")
            all_critical_ok = False
        
        # 2. FFprobe
        ffprobe_info = report['ffprobe']
        if ffprobe_info['found']:
            self.ffmpeg_status_label.configure(text=f"FFmpeg/FFprobe: Found (v{ffprobe_info.get('version', 'Unknown')})", text_color=SUCCESS_TEXT_COLOR)
            summary_messages.append("✓ FFprobe found.")
        else:
            self.ffmpeg_status_label.configure(text=f"FFmpeg/FFprobe: Not Found!", text_color=WARNING_TEXT_COLOR)
            summary_messages.append("⚠ WARNING: FFprobe not found. Media duration/progress may be inaccurate.")
            # Not treating as critical for app to run, but functionality is impaired

        # Model status will be updated by load_whisper_model_threaded callback
        self.model_status_label.configure(text=f"Whisper Model ('{config.DEFAULT_WHISPER_MODEL}'): Initializing...")

        # Update overall summary label in system check box
        if not all_critical_ok:
            final_summary = "Critical pre-requisites not met (see red items).\nApplication may not function correctly."
            self.summary_status_label.configure(text=final_summary, text_color=FAILURE_TEXT_COLOR)
        else:
            self.summary_status_label.configure(text="Basic system checks look OK.\nInitializing Whisper model...", text_color=SUCCESS_TEXT_COLOR)
        
        self.system_checks_passed_critically = all_critical_ok


    def open_link(self, url):
        try: webbrowser.open_new_tab(url)
        except Exception as e: print(f"Could not open link {url}: {e}")

    def update_status_from_thread(self, message_data): # Expects dict or string
        """Handles status updates from model loading and system checks."""
        if isinstance(message_data, dict): # For structured messages from Whisper init
            message = message_data.get("message", "Status update.")
            is_error = message_data.get("is_error", False)
            is_model_status = message_data.get("is_model_status", False) # Custom flag
        else: # For simple string messages
            message = str(message_data)
            is_error = False # Assume not an error for simple strings
            is_model_status = False

        self.loading_status_label.configure(text=message) # Update main status label

        if is_model_status: 
            if "loaded successfully" in message.lower():
                self.model_status_label.configure(text=f"Whisper Model ('{config.DEFAULT_WHISPER_MODEL}'): Loaded", text_color=SUCCESS_TEXT_COLOR)
            elif "error" in message.lower() or "failed" in message.lower():
                self.model_status_label.configure(text=f"Whisper Model ('{config.DEFAULT_WHISPER_MODEL}'): Load Failed!", text_color=FAILURE_TEXT_COLOR)
            else: # Intermediate status
                 self.model_status_label.configure(text=f"Whisper Model ('{config.DEFAULT_WHISPER_MODEL}'): {message[:30]}...", text_color=config.CHILD_TEXT_COLOR)


    def load_whisper_model_threaded(self):
        self.update_status_from_thread({"message": "Initializing transcription engine (this may take a moment)...", "is_model_status": True})
        
        def _load_model():
            # Wrapper for status_callback to add 'is_model_status' flag
            def model_status_cb(msg):
                if isinstance(msg, str):
                    self.update_status_from_thread({"message": msg, "is_model_status": True, "is_error": "error" in msg.lower() or "failed" in msg.lower()})
                elif isinstance(msg, dict):
                    msg["is_model_status"] = True
                    self.update_status_from_thread(msg)

            self.model_load_success = transcription_handler.initialize_whisper_model(
                model_name=config.DEFAULT_WHISPER_MODEL,
                status_callback=model_status_cb
            )
            self.model_loaded_event.set()
        
        thread = threading.Thread(target=_load_model, daemon=True)
        thread.start()

    def animate_progress_to_target(self, target_progress, on_complete_callback=None):
        if self.current_progress < target_progress:
            self.current_progress += 0.01
            self.current_progress = min(self.current_progress, target_progress)
            self.progress_bar.set(self.current_progress)
            self.after(20, lambda: self.animate_progress_to_target(target_progress, on_complete_callback))
        else:
            self.progress_bar.set(target_progress)
            self.current_progress = target_progress
            if on_complete_callback:
                on_complete_callback()

    def process_loading_steps(self):
        if self.current_step_index < len(self.loading_steps):
            status_text, target_progress, task_function = self.loading_steps[self.current_step_index]
            
            # For the main status label below progress bar
            self.loading_status_label.configure(text=status_text)
            
            def step_animation_complete():
                if task_function:
                    if task_function == self.load_whisper_model_threaded:
                        self.model_loaded_event.clear()
                        task_function()
                        self.wait_for_model_and_proceed(target_progress)
                    else: # For other synchronous tasks like run_system_checks
                        task_function()
                        self.current_step_index += 1
                        self.process_loading_steps()
                else: # No task, just update progress and move to next step
                    self.current_step_index += 1
                    self.process_loading_steps()

            self.animate_progress_to_target(target_progress, on_complete_callback=step_animation_complete)
        else: # All steps done
            final_load_status = "Loading Complete!"
            overall_readiness = self.system_checks_passed_critically and self.model_load_success

            if not self.system_checks_passed_critically:
                final_load_status = "System pre-requisites failed. Check details."
                self.continue_button.configure(text="Exit (Req. Failed)", fg_color="red", command=self.master.destroy) # Make it an exit button
            elif not self.model_load_success:
                final_load_status = "Critical: Transcription model failed to load."
                self.continue_button.configure(text="Exit (Model Error)", fg_color="red", command=self.master.destroy)
            
            self.update_status_from_thread(final_load_status) # For main status label
            self.progress_bar.set(1)
            
            if overall_readiness:
                self.continue_button.configure(state="normal")
            else:
                self.continue_button.configure(state="normal") # Still enable to allow exit command

            if self.on_load_complete_callback:
                self.on_load_complete_callback(overall_readiness)


    def wait_for_model_and_proceed(self, step_target_progress):
        if self.model_loaded_event.is_set():
            if not self.model_load_success:
                
                
                self.model_status_label.configure(text=f"Whisper Model ('{config.DEFAULT_WHISPER_MODEL}'): Load FAILED!", text_color=FAILURE_TEXT_COLOR)
            
            self.progress_bar.set(step_target_progress)
            self.current_progress = step_target_progress
            self.current_step_index += 1
            self.process_loading_steps() # Proceed to next loading step
        else:
            self.after(100, lambda: self.wait_for_model_and_proceed(step_target_progress))

    def handle_continue(self):
        
        print("Continue button clicked!")
        if self.on_continue_callback:
            self.on_continue_callback()