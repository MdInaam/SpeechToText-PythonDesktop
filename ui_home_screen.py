# ui_home_screen.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import app_config as config
from PIL import Image

import transcription_handler
import file_export_handler
import threading
from ui_transcription_popup import TranscriptionPopup
import utils

class HomeScreen(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=config.WINDOW_BG_COLOR, **kwargs)

        self.selected_files = []
        self.output_directory = os.path.join(os.path.expanduser("~"), "Downloads")
        self.transcription_thread = None
        self.transcription_popup_window = None
        self.file_durations_map = {}
        self.total_estimated_duration = 0.0

        self.audio_icon_image = None
        self.video_icon_image = None
        try:
            pil_audio_icon = Image.open(config.AUDIO_ICON_PATH).resize((20, 20), Image.Resampling.LANCZOS)
            self.audio_icon_image = ctk.CTkImage(light_image=pil_audio_icon, dark_image=pil_audio_icon)
        except Exception as e:
            print(f"Error loading audio icon: {e}")
        try:
            pil_video_icon = Image.open(config.VIDEO_ICON_PATH).resize((20, 20), Image.Resampling.LANCZOS)
            self.video_icon_image = ctk.CTkImage(light_image=pil_video_icon, dark_image=pil_video_icon)
        except Exception as e:
            print(f"Error loading video icon: {e}")

        self.audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac']
        self.video_extensions = ['.mp4', '.mkv', '.mov', '.avi', '.flv', '.wmv']

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(expand=True, fill="both", padx=20, pady=15)
        self.top_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.top_frame.pack(side="top", fill="both", expand=True, pady=(0, 10))
        self.middle_frame = ctk.CTkFrame(self.content_frame, fg_color=config.BOX_BG_COLOR, corner_radius=config.SCROLLABLE_FRAME_STYLE.get("corner_radius", 10))
        self.middle_frame.pack(side="top", fill="x", pady=10, ipady=10)
        self.bottom_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.bottom_frame.pack(side="bottom", fill="x", pady=(10, 0))

        self.files_display_frame_label = ctk.CTkLabel(self.top_frame, text="Selected Files:", font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=16, weight="bold"), text_color=config.CHILD_TEXT_COLOR, anchor="w")
        self.files_display_frame_label.pack(side="top", fill="x", pady=(0,5))
        self.files_display_frame = ctk.CTkScrollableFrame(self.top_frame, fg_color=config.BOX_BG_COLOR, corner_radius=config.SCROLLABLE_FRAME_STYLE.get("corner_radius", 10))
        self.files_display_frame.pack(side="top", fill="both", expand=True, pady=(0,10))
        self.no_files_label = ctk.CTkLabel(self.files_display_frame, text="No files selected.", text_color=config.PLACEHOLDER_TEXT_COLOR, font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=12))
        self.no_files_label.pack(pady=10, padx=10, expand=True)
        self.add_file_button = ctk.CTkButton(self.top_frame, text="Add File(s)", command=self.select_files, font=ctk.CTkFont(family=config.BUTTON_FONT_TUPLE[0], size=config.BUTTON_FONT_TUPLE[1], weight=config.BUTTON_FONT_TUPLE[2]), height=35, **config.DEFAULT_BUTTON_STYLE)
        self.add_file_button.pack(side="top", pady=(5,0))

        self.middle_frame.grid_columnconfigure(1, weight=1)
        self.output_format_label = ctk.CTkLabel(self.middle_frame, text="Output Format:", font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=14), text_color=config.CHILD_TEXT_COLOR)
        self.output_format_label.grid(row=0, column=0, padx=(15,5), pady=10, sticky="w")
        self.output_format_combobox = ctk.CTkComboBox(self.middle_frame, values=["Word (.docx)", "PDF (.pdf)"], font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=14), dropdown_font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=14), border_color=config.BUTTON_PRIMARY_COLOR, button_color=config.BUTTON_PRIMARY_COLOR, button_hover_color=config.BUTTON_HOVER_COLOR, state="readonly", height=30)
        self.output_format_combobox.set("Word (.docx)")
        self.output_format_combobox.grid(row=0, column=1, columnspan=2, padx=(0,15), pady=10, sticky="ew")
        self.output_name_label = ctk.CTkLabel(self.middle_frame, text="Output Filename:", font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=14), text_color=config.CHILD_TEXT_COLOR)
        self.output_name_label.grid(row=1, column=0, padx=(15,5), pady=10, sticky="w")
        self.output_name_entry = ctk.CTkEntry(self.middle_frame, placeholder_text="Name your file (if not separate)", font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=14), border_color=config.BUTTON_PRIMARY_COLOR, height=30)
        self.output_name_entry.grid(row=1, column=1, columnspan=2, padx=(0,15), pady=10, sticky="ew")
        self.separate_files_checkbox = ctk.CTkCheckBox(self.middle_frame, text="Separate file for each audio/video?", font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=14), text_color=config.CHILD_TEXT_COLOR, checkbox_height=20, checkbox_width=20, border_color=config.BUTTON_PRIMARY_COLOR, hover_color=config.BUTTON_HOVER_COLOR, fg_color=config.BUTTON_PRIMARY_COLOR, command=self.toggle_filename_entry_state)
        self.separate_files_checkbox.grid(row=2, column=0, columnspan=3, padx=15, pady=10, sticky="w")
        self.output_dir_label_text = ctk.CTkLabel(self.middle_frame, text="Save Location:", font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=14), text_color=config.CHILD_TEXT_COLOR)
        self.output_dir_label_text.grid(row=3, column=0, padx=(15,5), pady=10, sticky="w")
        self.output_dir_display_label = ctk.CTkEntry(self.middle_frame, font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=12), border_color=config.BUTTON_PRIMARY_COLOR, text_color=config.SUB_CHILD_TEXT_COLOR, height=30, state="readonly")
        self.output_dir_display_label.grid(row=3, column=1, padx=(0,5), pady=10, sticky="ew")
        self.output_dir_button = ctk.CTkButton(self.middle_frame, text="Browse", command=self.select_output_directory, font=ctk.CTkFont(family=config.BUTTON_FONT_TUPLE[0], size=12, weight=config.BUTTON_FONT_TUPLE[2]), width=80, height=30, **config.DEFAULT_BUTTON_STYLE)
        self.output_dir_button.grid(row=3, column=2, padx=(0,15), pady=10, sticky="e")

        self.bottom_frame.grid_columnconfigure((0, 1), weight=1)
        self.transcribe_button = ctk.CTkButton(self.bottom_frame, text="Transcribe", command=self.start_transcription_process, font=ctk.CTkFont(family=config.BUTTON_FONT_TUPLE[0], size=config.BUTTON_FONT_TUPLE[1], weight=config.BUTTON_FONT_TUPLE[2]), height=40, **config.DEFAULT_BUTTON_STYLE)
        self.transcribe_button.grid(row=0, column=0, padx=(0,10), pady=5, sticky="ew")
        self.clear_button = ctk.CTkButton(self.bottom_frame, text="Clear Fields", command=self.clear_fields_action, font=ctk.CTkFont(family=config.BUTTON_FONT_TUPLE[0], size=config.BUTTON_FONT_TUPLE[1], weight=config.BUTTON_FONT_TUPLE[2]), height=40, fg_color=config.ACCENT_COLOR, hover_color=config.BUTTON_HOVER_COLOR, text_color=config.CHILD_TEXT_COLOR, corner_radius=config.DEFAULT_BUTTON_STYLE.get("corner_radius", 8))
        self.clear_button.grid(row=0, column=1, padx=(10,0), pady=5, sticky="ew")

        self.toggle_filename_entry_state()
        self.update_output_dir_display()

    def select_files(self):
        filetypes = [("Media files", "*.mp3 *.wav *.m4a *.flac *.ogg *.mp4 *.mkv *.mov *.avi *.webm"), ("Audio files", "*.mp3 *.wav *.m4a *.flac *.ogg *.aac"), ("Video files", "*.mp4 *.mkv *.mov *.avi *.webm *.flv"), ("All files", "*.*")]
        filepaths = filedialog.askopenfilenames(title="Select Audio/Video Files", filetypes=filetypes)
        if filepaths:
            new_files = [fp for fp in filepaths if fp not in self.selected_files]
            self.selected_files.extend(new_files)
            self.update_selected_files_display()
        print(f"Selected files: {self.selected_files}")

    def get_file_icon(self, filepath):
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        if ext in self.audio_extensions: return self.audio_icon_image
        elif ext in self.video_extensions: return self.video_icon_image
        return None

    def update_selected_files_display(self):
        for widget in self.files_display_frame.winfo_children(): widget.destroy()
        if not self.selected_files:
            self.no_files_label = ctk.CTkLabel(self.files_display_frame, text="No files selected.", text_color=config.PLACEHOLDER_TEXT_COLOR, font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=12))
            self.no_files_label.pack(pady=10, padx=10, expand=True)
            return
        for filepath in self.selected_files:
            filename = os.path.basename(filepath)
            file_entry_frame = ctk.CTkFrame(self.files_display_frame, fg_color="transparent")
            file_entry_frame.pack(fill="x", pady=2, padx=2)
            icon_to_display = self.get_file_icon(filepath)
            if icon_to_display:
                icon_label = ctk.CTkLabel(file_entry_frame, image=icon_to_display, text="")
                icon_label.pack(side="left", padx=(0, 5))
            else:
                icon_label = ctk.CTkLabel(file_entry_frame, text="?", width=20, font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=12))
                icon_label.pack(side="left", padx=(0, 5))
            text_label = ctk.CTkLabel(file_entry_frame, text=filename, font=ctk.CTkFont(family=config.FONT_FAMILY_POPPINS, size=12), text_color=config.SUB_CHILD_TEXT_COLOR, anchor="w")
            text_label.pack(side="left", fill="x", expand=True, padx=(5,0))
            remove_btn = ctk.CTkButton(file_entry_frame, text="X", width=25, height=25, text_color=config.CHILD_TEXT_COLOR, fg_color=config.ACCENT_COLOR, hover_color="red", command=lambda fp=filepath: self.remove_selected_file(fp))
            remove_btn.pack(side="right", padx=5)

    def remove_selected_file(self, filepath_to_remove):
        if filepath_to_remove in self.selected_files:
            self.selected_files.remove(filepath_to_remove)
            self.update_selected_files_display()
        print(f"Removed file: {filepath_to_remove}")

    def toggle_filename_entry_state(self):
        if self.separate_files_checkbox.get() == 1:
            self.output_name_entry.configure(state="disabled", placeholder_text="Uses original filenames")
            self.output_name_entry.delete(0, "end")
        else:
            self.output_name_entry.configure(state="normal", placeholder_text="Name your file (if not separate)")

    def update_output_dir_display(self):
        self.output_dir_display_label.configure(state="normal")
        self.output_dir_display_label.delete(0, "end")
        if self.output_directory:
            self.output_dir_display_label.insert(0, self.output_directory)
            self.output_dir_display_label.configure(text_color=config.SUB_CHILD_TEXT_COLOR)
        else:
            self.output_dir_display_label.insert(0, "Default: Downloads folder")
            self.output_dir_display_label.configure(text_color=config.PLACEHOLDER_TEXT_COLOR)
        self.output_dir_display_label.configure(state="readonly")

    def select_output_directory(self):
        directory = filedialog.askdirectory(title="Select Output Directory", initialdir=self.output_directory if self.output_directory else os.path.expanduser("~"))
        if directory:
            self.output_directory = directory
            self.update_output_dir_display()
        print(f"Selected output directory: {self.output_directory}")

    def start_transcription_process(self):
        if not self.selected_files:
            messagebox.showerror("Input Error", "No files selected for transcription.")
            return
        if not self.output_directory:
            messagebox.showerror("Input Error", "Please select an output directory.")
            return
        is_separate_files = self.separate_files_checkbox.get() == 1
        output_filename_base = self.output_name_entry.get().strip()
        if not is_separate_files and not output_filename_base:
            messagebox.showerror("Input Error", "Please provide an output filename if not creating separate files.")
            return
        if self.transcription_thread and self.transcription_thread.is_alive():
            messagebox.showwarning("In Progress", "A transcription process is already running.")
            return

        self.file_durations_map = {}
        self.total_estimated_duration = 0.0
        files_with_unknown_duration = []

        if self.transcription_popup_window is None or not self.transcription_popup_window.winfo_exists():
            self.transcription_popup_window = TranscriptionPopup(
                master=self.winfo_toplevel(),
                total_files=len(self.selected_files),
                output_folder_path=self.output_directory,
                total_estimated_duration_seconds=1 # Initial dummy value, will be updated
            )
            self.transcription_popup_window.grab_set()
        else:
            self.transcription_popup_window.lift()

        self.transcription_popup_window.after(0, lambda: self.transcription_popup_window.update_overall_status(0))
        self.transcription_popup_window.after(0, lambda: self.transcription_popup_window.update_current_action("Calculating file durations..."))
        self.transcription_popup_window.after(0, lambda: self.transcription_popup_window.update_detailed_progress(""))
        self.transcription_popup_window.after(0, lambda: self.transcription_popup_window.update_progress_bar_value(0.01))

        print("Calculating media durations...")
        for fp_idx, fp in enumerate(self.selected_files):
            duration = utils.get_media_duration(fp)
            if duration <= 0:
                files_with_unknown_duration.append(os.path.basename(fp))
                print(f"Warning: Could not determine duration for {os.path.basename(fp)} or it's zero.")
                self.file_durations_map[fp] = 30.0 # Assign a default duration for progress calculation
                self.total_estimated_duration += 30.0
            else:
                self.file_durations_map[fp] = duration
                self.total_estimated_duration += duration

        if files_with_unknown_duration:
            messagebox.showwarning("Duration Warning", f"Could not determine duration for:\n{', '.join(files_with_unknown_duration)}\nUsing a default of 30s for progress estimation for these files.")

        print(f"Total estimated duration for transcription: {self.total_estimated_duration:.2f} seconds")

        if self.transcription_popup_window and self.transcription_popup_window.winfo_exists():
            self.transcription_popup_window.total_estimated_duration_seconds = self.total_estimated_duration
            self.transcription_popup_window.after(0, lambda: self.transcription_popup_window.update_progress_bar_value(0.02)) # Small initial bump

        transcription_args = {
            "files_to_process": list(self.selected_files),
            "output_dir": self.output_directory,
            "output_format_str": self.output_format_combobox.get(),
            "is_separate": is_separate_files,
            "base_filename_user": output_filename_base,
            "popup_window": self.transcription_popup_window,
            "file_durations_map": self.file_durations_map.copy(),
            "total_duration_all_files": self.total_estimated_duration
        }
        self.transcription_thread = threading.Thread(target=self._transcription_worker, kwargs=transcription_args, daemon=True)
        self.transcription_thread.start()

    def _transcription_worker(self, files_to_process, output_dir, output_format_str,
                              is_separate, base_filename_user, popup_window,
                              file_durations_map, total_duration_all_files):

        overall_success = True
        # THIS STORES THE SUM OF DURATIONS OF *PREVIOUSLY FULLY COMPLETED* FILES
        accumulated_duration_of_completed_files = 0.0
        all_text_combined = []

        try:
            for i, input_filepath in enumerate(files_to_process):
                if not popup_window.winfo_exists() or popup_window.cancel_requested.is_set():
                    popup_window.after(0, lambda: popup_window.update_current_action("Cancellation acknowledged. Stopping..."))
                    overall_success = False
                    break

                current_file_duration = file_durations_map.get(input_filepath, 30.0)
                if current_file_duration <= 0: current_file_duration = 30.0

                filename_only = os.path.basename(input_filepath)
                file_base_name, _ = os.path.splitext(filename_only)

                # Tracks how much of the CURRENT file has been processed via segments
                # This is reset for each new file.
                processed_time_for_current_file_via_segments = 0.0

                popup_window.after(0, lambda current_idx=i + 1: popup_window.update_overall_status(current_idx))
                popup_window.after(0, lambda fn=filename_only: popup_window.update_current_action(f"Starting: {fn}"))
                popup_window.after(0, lambda: popup_window.update_detailed_progress("")) # Clear details for new file


                def handle_transcription_progress_update(data_dict):
                    if not popup_window.winfo_exists(): return

                    nonlocal overall_success
                    # We need to update processed_time_for_current_file_via_segments
                    # and use accumulated_duration_of_completed_files (read-only here)
                    nonlocal processed_time_for_current_file_via_segments

                    if data_dict['type'] == 'segment':
                        segment_line = data_dict.get('full_line', 'Processing segment...')
                        segment_end_s = data_dict.get('end_seconds', 0.0)

                        # Update how much of the *current* file has been processed
                        processed_time_for_current_file_via_segments = min(segment_end_s, current_file_duration)

                        popup_window.after(0, lambda txt=segment_line: popup_window.update_detailed_progress(txt))

                        if total_duration_all_files > 0:
                            # Overall progress:
                            # Time from (previously) completed files + progress in current file
                            current_total_processed_time_for_all_files = accumulated_duration_of_completed_files + processed_time_for_current_file_via_segments
                            overall_progress_value = min(1.0, current_total_processed_time_for_all_files / total_duration_all_files)

                            # DEBUG PRINT FOR UI PROGRESS VALUES
                            print(f"UI_HOME_SCREEN DEBUG: acc_dur_completed={accumulated_duration_of_completed_files:.2f}, "
                                  f"proc_time_current_seg={processed_time_for_current_file_via_segments:.2f}, "
                                  f"total_proc_all={current_total_processed_time_for_all_files:.2f}, "
                                  f"overall_val={overall_progress_value:.4f}")

                            popup_window.after(0, lambda p=overall_progress_value: popup_window.update_progress_bar_value(p))

                    elif data_dict['type'] == 'status':
                        status_msg = data_dict['message']
                        # Simple heuristic to decide where to show status
                        if "transcription started for" in status_msg.lower() or \
                           "finished" in status_msg.lower() or \
                           "saving" in status_msg.lower() or \
                           "error" in status_msg.lower() or \
                           "failed" in status_msg.lower():
                             popup_window.after(0, lambda msg=status_msg: popup_window.update_current_action(msg))
                        else: # Whisper's language detection etc.
                            popup_window.after(0, lambda msg=status_msg: popup_window.update_detailed_progress(msg))

                        if data_dict.get('is_error'):
                            overall_success = False
                # --- END Progress callback ---

                transcribed_text = transcription_handler.transcribe_media_file(
                    input_filepath,
                    progress_callback=handle_transcription_progress_update,
                    verbose_transcription=True
                )

                if not popup_window.winfo_exists() or popup_window.cancel_requested.is_set():
                    if popup_window.winfo_exists() and popup_window.cancel_requested.is_set():
                         # If cancelled, add the portion of the current file that was actually processed
                        accumulated_duration_of_completed_files += processed_time_for_current_file_via_segments
                    overall_success = False; break


                if transcribed_text is None: # Transcription failed for this file
                    popup_window.after(0, lambda fn=filename_only: popup_window.update_detailed_progress(f"Failed to transcribe {fn}. Skipping."))
                    overall_success = False
                    # Add the actual processed part of THIS FAILED file to the accumulated time
                    accumulated_duration_of_completed_files += processed_time_for_current_file_via_segments
                else: # Transcription succeeded for this file
                    # File Saving Logic
                    if is_separate:
                        current_output_filename = f"{file_base_name}.docx" if "Word" in output_format_str else f"{file_base_name}.pdf"
                        output_filepath_full = os.path.join(output_dir, current_output_filename)
                        popup_window.after(0, lambda fn=current_output_filename: popup_window.update_current_action(f"Saving: {fn}..."))

                        save_successful = False
                        status_saver_cb = lambda msg_data: popup_window.after(0, lambda m=(msg_data if isinstance(msg_data, dict) else {'type':'status', 'message': str(msg_data)}).get('message', str(msg_data)): popup_window.update_detailed_progress(m))

                        if "Word" in output_format_str:
                            save_successful = file_export_handler.save_text_to_word(transcribed_text, output_filepath_full, status_callback=status_saver_cb)
                        else:
                            save_successful = file_export_handler.save_text_to_pdf(transcribed_text, output_filepath_full, status_callback=status_saver_cb)
                        if not save_successful:
                            overall_success = False
                            popup_window.after(0, lambda fn=current_output_filename: popup_window.update_detailed_progress(f"Failed to save {fn}."))
                    else:
                        all_text_combined.append(f"--- Transcription for {filename_only} ---\n{transcribed_text}\n\n")


                    accumulated_duration_of_completed_files += current_file_duration


                # Update progress bar to reflect completion of this file's contribution before starting next

                if total_duration_all_files > 0:
                    progress_val = min(1.0, accumulated_duration_of_completed_files / total_duration_all_files)
                    print(f"UI_HOME_SCREEN DEBUG (End of File {i+1}): acc_dur_completed={accumulated_duration_of_completed_files:.2f}, "
                          f"final_file_progress_val={progress_val:.4f}")
                    popup_window.after(0, lambda p=progress_val: popup_window.update_progress_bar_value(p))


            # After the loop, if not creating separate files, save the combined content
            if not is_separate and all_text_combined:
                if not popup_window.winfo_exists() or popup_window.cancel_requested.is_set(): overall_success = False
                else:
                    combined_output_filename = f"{base_filename_user}.docx" if "Word" in output_format_str else f"{base_filename_user}.pdf"
                    combined_output_filepath_full = os.path.join(output_dir, combined_output_filename)
                    popup_window.after(0, lambda fn=combined_output_filename: popup_window.update_current_action(f"Saving combined file: {fn}..."))
                    combined_text_str = "".join(all_text_combined)

                    status_saver_cb_combined = lambda msg_data: popup_window.after(0, lambda m=(msg_data if isinstance(msg_data, dict) else {'type':'status', 'message': str(msg_data)}).get('message', str(msg_data)): popup_window.update_detailed_progress(m))

                    save_successful = False
                    if "Word" in output_format_str:
                        save_successful = file_export_handler.save_text_to_word(combined_text_str, combined_output_filepath_full, status_callback=status_saver_cb_combined)
                    else:
                        save_successful = file_export_handler.save_text_to_pdf(combined_text_str, combined_output_filepath_full, status_callback=status_saver_cb_combined)
                    if not save_successful:
                        overall_success = False
                        popup_window.after(0, lambda fn=combined_output_filename: popup_window.update_detailed_progress(f"Failed to save {fn}."))

            if overall_success and not popup_window.cancel_requested.is_set() and total_duration_all_files > 0:
                 popup_window.after(0, lambda: popup_window.update_progress_bar_value(1.0))

        except Exception as e:
            if popup_window.winfo_exists():
                popup_window.after(0, lambda err=str(e): popup_window.update_detailed_progress(f"An error occurred in worker: {err}"))
            print(f"Error in transcription worker (ui_home_screen.py): {e}") # Log to console
            import traceback
            traceback.print_exc() # Print full traceback
            overall_success = False
        finally:
            if popup_window.winfo_exists():
                final_success_state = overall_success and not popup_window.cancel_requested.is_set()
                popup_window.after(0, lambda s=final_success_state: popup_window.process_complete(s))



    def clear_fields_action(self):
        print("--- Clear Fields Button Clicked ---")
        self.selected_files = []
        self.update_selected_files_display()
        self.output_format_combobox.set("Word (.docx)")
        self.separate_files_checkbox.deselect()
        self.toggle_filename_entry_state()
        self.output_name_entry.delete(0, "end")
        self.output_directory = os.path.join(os.path.expanduser("~"), "Downloads")
        self.update_output_dir_display()
        print("Fields cleared.")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.geometry("960x650") 
    root.title("Home Screen Test")
    try:
        if hasattr(ctk, 'FontManager') and hasattr(ctk.FontManager, 'load_font'):
            ctk.FontManager.load_font(config.POPPINS_BOLD_PATH)
            ctk.FontManager.load_font(config.POPPINS_REGULAR_PATH)
        else:
            print("CTk.FontManager not available or load_font method missing.")
    except Exception as e:
        print(f"Error loading Poppins fonts for standalone test: {e}")
    home_frame = HomeScreen(master=root)
    home_frame.pack(expand=True, fill="both")
    root.mainloop()