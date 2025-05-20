import subprocess
import json
import os

def get_media_duration(filepath: str) -> float:
    """
    Gets the duration of a media file in seconds using ffprobe.
    Returns 0.0 if duration cannot be determined or ffprobe fails.
    """
    if not os.path.exists(filepath):
        
        print(f"Utils - Error: File not found for duration check: {filepath}")
        return 0.0

    command = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",      
        "-show_streams",     
        filepath
    ]
    try:
        # Using shell=False (default) and passing command as a list is safer
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        data = json.loads(result.stdout)
        
        duration = None
        # Prefer duration from the format section
        if 'format' in data and 'duration' in data['format']:
            duration_str = data['format'].get('duration')
            if duration_str:
                try:
                    duration = float(duration_str)
                except ValueError:
                    print(f"Utils - Warning: Could not parse format duration '{duration_str}' as float for {os.path.basename(filepath)}")
                    duration = None # Ensure duration is None if parsing fails
        
        # Fallback to stream duration if format duration is not available or zero, or failed parsing
        if (duration is None or duration <= 0.0) and 'streams' in data and data['streams']:
            for stream in data['streams']:
                
                if stream.get('codec_type') in ['audio', 'video'] and 'duration' in stream:
                    duration_str = stream.get('duration')
                    if duration_str:
                        try:
                            duration = float(duration_str)
                            break 
                        except ValueError:
                            print(f"Utils - Warning: Could not parse stream duration '{duration_str}' as float for {os.path.basename(filepath)}")
                            duration = None 
                            continue 
        
        return duration if duration is not None and duration > 0.0 else 0.0

    except FileNotFoundError:

        print("Utils - Error: ffprobe command not found. Please ensure FFmpeg is installed and in system PATH.")
        return 0.0
    except subprocess.CalledProcessError as e:
        
        print(f"Utils - Error getting duration for '{os.path.basename(filepath)}' with ffprobe. stderr: {e.stderr.strip()}")
        return 0.0
    except json.JSONDecodeError:
        print(f"Utils - Error decoding JSON output from ffprobe for '{os.path.basename(filepath)}'.")
        return 0.0
    except Exception as e:
        print(f"Utils - An unexpected error occurred while getting duration for '{os.path.basename(filepath)}': {e}")
        return 0.0