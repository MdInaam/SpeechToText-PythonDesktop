import whisper
import app_config as config
import torch
import os
import sys
import io
import threading
import re
import time
import unicodedata

WHISPER_MODEL = None
MODEL_LOADED_SUCCESSFULLY = False
DEVICE_USED = None

def initialize_whisper_model(model_name: str = None, status_callback=None):
    global WHISPER_MODEL, MODEL_LOADED_SUCCESSFULLY, DEVICE_USED
    if MODEL_LOADED_SUCCESSFULLY and WHISPER_MODEL is not None and DEVICE_USED == "cuda":
        if status_callback:
            status_callback(f"Whisper model '{model_name or config.DEFAULT_WHISPER_MODEL}' already loaded on CUDA.")
        return True
    selected_model = model_name if model_name else config.DEFAULT_WHISPER_MODEL
    if status_callback:
        status_callback(f"Initializing Whisper model: {selected_model} for CUDA...")
    if not torch.cuda.is_available():
        error_msg = "Error: CUDA is not available on this system. GPU acceleration is required."
        if status_callback:
            status_callback(error_msg)
            status_callback("Ensure you have an NVIDIA GPU, latest drivers, and compatible CUDA Toolkit.")
            status_callback("Verify your PyTorch installation includes CUDA support.")
        print(error_msg)
        MODEL_LOADED_SUCCESSFULLY = False
        DEVICE_USED = "cpu_check_failed_cuda"
        return False
    DEVICE_USED = "cuda"
    if status_callback:
        status_callback(f"Attempting to load model on device: {DEVICE_USED.upper()}")
    try:
        WHISPER_MODEL = whisper.load_model(selected_model, device=DEVICE_USED)
        MODEL_LOADED_SUCCESSFULLY = True
        if status_callback:
            status_callback(f"Whisper model '{selected_model}' loaded successfully on {DEVICE_USED.upper()}.")
        print(f"Whisper model '{selected_model}' loaded successfully on {DEVICE_USED.upper()}.")
        return True
    except Exception as e:
        error_msg = f"Error loading Whisper model '{selected_model}' on CUDA: {e}"
        if "CUDA out of memory" in str(e):
            error_msg += "\nTry a smaller model or free up GPU memory."
        elif isinstance(e, FileNotFoundError):
            error_msg = f"Whisper model files for '{selected_model}' not found."
        if status_callback:
            status_callback(error_msg)
        print(error_msg)
        MODEL_LOADED_SUCCESSFULLY = False
        return False

def time_str_to_seconds(time_str: str) -> float:
    parts = time_str.split(':')
    try:
        if len(parts) == 3:
            h, m, s_ms = parts
            s, ms = s_ms.split('.')
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0
        elif len(parts) == 2:
            m, s_ms = parts
            s, ms = s_ms.split('.')
            return int(m) * 60 + int(s) + int(ms) / 1000.0
    except ValueError:
        print(f"Warning: Could not parse time string: {time_str}")
        return 0.0
    return 0.0

def parse_segment_line(line: str, original_stdout_for_debug=sys.stdout):
    normalized_line = unicodedata.normalize('NFC', line)
    cleaned_line = normalized_line.replace("\xa0", " ").replace("\r", "")
    stripped_line = cleaned_line.strip()
    pattern = r"^\[(\d{2}:\d{2}(?::\d{2})?\.\d{3})\s*-->\s*(\d{2}:\d{2}(?::\d{2})?\.\d{3})\]\s*(.*)$"
    segment_match = re.match(pattern, stripped_line)
    if segment_match:
        start_str, end_str, text_segment = segment_match.groups()
        try:
            start_seconds = time_str_to_seconds(start_str)
            end_seconds = time_str_to_seconds(end_str)
            return start_seconds, end_seconds, text_segment.strip(), stripped_line
        except Exception as e:
            print(f"Error in time_str_to_seconds: {e}", file=original_stdout_for_debug, flush=True)
            return None, None, None, stripped_line
    if stripped_line.startswith("Detecting language") or stripped_line.startswith("Detected language:"):
        return None, None, None, stripped_line
    if stripped_line:
        return None, None, None, stripped_line
    return None, None, None, None

def transcribe_media_file(file_path: str, language: str = None, task: str = "transcribe",
                          progress_callback=None, verbose_transcription: bool = True):
    global WHISPER_MODEL, MODEL_LOADED_SUCCESSFULLY, DEVICE_USED
    if not MODEL_LOADED_SUCCESSFULLY or WHISPER_MODEL is None or DEVICE_USED != "cuda":
        error_msg = "Error: Whisper model is not loaded on CUDA."
        if progress_callback:
            progress_callback({'type': 'status', 'message': error_msg, 'is_error': True})
        print(error_msg)
        return None
    if progress_callback:
        progress_callback({'type': 'status', 'message': f"Preparing: {os.path.basename(file_path)}..."})
    full_transcribed_text_from_result = None
    options = {"language": language, "task": task, "fp16": True, "verbose": verbose_transcription}
    options = {k: v for k, v in options.items() if v is not None}
    if verbose_transcription:
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        all_captured_lines = []
        last_segment_end_time = -1.0
        transcription_result_holder = {"result_obj": None, "error": None}
        def whisper_worker_function():
            try:
                transcription_result_holder["result_obj"] = WHISPER_MODEL.transcribe(file_path, **options)
            except Exception as e:
                transcription_result_holder["error"] = e
                print(f"Error during transcription: {e}", file=old_stdout, flush=True)
        whisper_thread = threading.Thread(target=whisper_worker_function, daemon=True)
        whisper_thread.start()
        if progress_callback:
            progress_callback({'type': 'status', 'message': f"Transcription started for: {os.path.basename(file_path)}..."})
        processed_lines_count = 0
        while whisper_thread.is_alive():
            whisper_thread.join(timeout=0.1)
            current_lines = redirected_output.getvalue().splitlines()
            if len(current_lines) > processed_lines_count:
                new_lines = current_lines[processed_lines_count:]
                for line in new_lines:
                    all_captured_lines.append(line)
                    start_s, end_s, text_seg, full_l_or_msg = parse_segment_line(line, old_stdout)
                    if start_s is not None and end_s is not None:
                        if end_s > last_segment_end_time and progress_callback:
                            progress_callback({'type': 'segment', 'start_seconds': start_s, 'end_seconds': end_s, 'text_segment': text_seg, 'full_line': full_l_or_msg})
                            last_segment_end_time = end_s
                    elif full_l_or_msg and progress_callback:
                        if not full_l_or_msg.strip().startswith("UI_HOME_SCREEN DEBUG:"):
                            progress_callback({'type': 'status', 'message': full_l_or_msg})
                processed_lines_count = len(current_lines)
            time.sleep(0.05)
        sys.stdout = old_stdout
        final_lines = redirected_output.getvalue().splitlines()[processed_lines_count:]
        for line in final_lines:
            start_s, end_s, text_seg, full_l_or_msg = parse_segment_line(line, old_stdout)
            if start_s is not None and end_s is not None and end_s > last_segment_end_time:
                if progress_callback:
                    progress_callback({'type': 'segment', 'start_seconds': start_s, 'end_seconds': end_s, 'text_segment': text_seg, 'full_line': full_l_or_msg})
                last_segment_end_time = end_s
            elif full_l_or_msg and progress_callback:
                if not full_l_or_msg.strip().startswith("UI_HOME_SCREEN DEBUG:"):
                    progress_callback({'type': 'status', 'message': full_l_or_msg})
        redirected_output.close()
        if transcription_result_holder["error"]:
            error_msg = f"Error during transcription: {transcription_result_holder['error']}"
            if progress_callback:
                progress_callback({'type': 'status', 'message': error_msg, 'is_error': True})
            print(error_msg, file=sys.stderr)
            return None
        if transcription_result_holder["result_obj"]:
            full_transcribed_text_from_result = transcription_result_holder["result_obj"]["text"]
        else:
            error_msg = f"Transcription finished but no result object was found."
            if progress_callback:
                progress_callback({'type': 'status', 'message': error_msg, 'is_error': True})
            print(error_msg, file=sys.stderr)
            return None
    else:
        try:
            if progress_callback:
                progress_callback({'type': 'status', 'message': f"Transcription started for: {os.path.basename(file_path)} (non-verbose)..."})
            result_obj = WHISPER_MODEL.transcribe(file_path, **options)
            full_transcribed_text_from_result = result_obj["text"]
        except Exception as e:
            error_msg = f"Error during transcription: {e}"
            if progress_callback:
                progress_callback({'type': 'status', 'message': error_msg, 'is_error': True})
            print(error_msg, file=sys.stderr)
            return None
    if full_transcribed_text_from_result is not None:
        if progress_callback:
            progress_callback({'type': 'status', 'message': f"Finished: {os.path.basename(file_path)}."})
        return full_transcribed_text_from_result.strip()
    else:
        if not verbose_transcription and progress_callback:
            progress_callback({'type': 'status', 'message': f"Failed to transcribe: {os.path.basename(file_path)}.", 'is_error': True})
        return None
