import sys
import platform
import subprocess
import shutil # For shutil.which
import re

def _run_command(command_parts):
    """
    Helper function to run a shell command (list of parts) and return its output.
    Returns a tuple: (success: bool, output_or_error: str)
    """
    try:
        process = subprocess.run(command_parts, check=False, capture_output=True, text=True, encoding='utf-8')
        if process.returncode == 0:
            return True, process.stdout.strip()
        else:
            # Try to provide a more informative error including stderr if available
            error_message = f"Command '{' '.join(command_parts)}' failed with code {process.returncode}."
            if process.stderr:
                error_message += f" Error: {process.stderr.strip()}"
            elif process.stdout: # Sometimes errors go to stdout
                error_message += f" Output: {process.stdout.strip()}"
            return False, error_message
    except FileNotFoundError:
        return False, f"'{command_parts[0]}' not found. Ensure it's installed and in PATH."
    except Exception as e:
        return False, f"An unexpected error occurred running '{' '.join(command_parts)}': {str(e)}"

def get_python_info():
    """Gathers basic Python and OS information."""
    return {
        "python_version": platform.python_version(), # More concise than sys.version
        "operating_system": f"{platform.system()} {platform.release()} ({platform.machine()})"
    }

def get_pytorch_info():
    """Gathers PyTorch and CUDA (via PyTorch) information."""
    info = {"installed": False, "error_message": None}
    try:
        import torch
        info["installed"] = True
        info["version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()

        if info["cuda_available"]:
            info["cuda_version_pytorch"] = torch.version.cuda if torch.version.cuda else "N/A"
            info["gpu_count"] = torch.cuda.device_count()
            gpus = []
            for i in range(info["gpu_count"]):
                gpu_details = {"name": torch.cuda.get_device_name(i)}
                try:
                    props = torch.cuda.get_device_properties(i)
                    gpu_details["capability"] = f"{props.major}.{props.minor}"
                    gpu_details["memory_mb"] = f"{props.total_memory / (1024**2):.0f}"
                except Exception:
                    gpu_details["capability"] = "N/A"
                    gpu_details["memory_mb"] = "N/A"
                gpus.append(gpu_details)
            info["gpus"] = gpus
        else:
            info["cuda_status_message"] = "CUDA not available via PyTorch (CPU-only PyTorch or driver/toolkit issue)."

    except ImportError:
        info["error_message"] = "PyTorch is NOT installed."
    except Exception as e:
        info["error_message"] = f"Error checking PyTorch: {str(e)}"
    return info

def get_nvidia_driver_info():
    """Attempts to get NVIDIA driver version using nvidia-smi."""
    info = {"driver_version": "N/A", "status_message": "nvidia-smi not found or failed."}
    nvidia_smi_path = shutil.which("nvidia-smi")
    if nvidia_smi_path:
        success, output = _run_command([nvidia_smi_path, "--query-gpu=driver_version", "--format=csv,noheader"])
        if success:
            info["driver_version"] = output.strip()
            info["status_message"] = "Detected"
        else:
            info["status_message"] = f"nvidia-smi failed: {output}"
    return info

def check_ffprobe_availability():
    """Checks if ffprobe is accessible and executable."""
    info = {"found": False, "status_message": "ffprobe not found."}
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        success, output = _run_command([ffprobe_path, "-version"])
        if success and "ffprobe version" in output.lower():
            info["found"] = True
            # Extract version from output if desired, e.g., using regex
            version_match = re.search(r"ffprobe version (\S+)", output, re.IGNORECASE)
            if version_match:
                info["version"] = version_match.group(1)
                info["status_message"] = f"Found (Version: {info['version']})"
            else:
                info["status_message"] = "Found (Version could not be parsed)"
        elif success: # Command ran but output unexpected
            info["status_message"] = f"ffprobe ran but version string not found. Output: {output[:100]}..."
        else: # Command failed
            info["status_message"] = f"ffprobe execution failed: {output}"
    else:
        info["status_message"] = "ffprobe not found in PATH. Media duration features will be affected."
    return info


def get_system_summary():
    """Consolidates all system checks into a single dictionary."""
    summary = {
        "python": get_python_info(),
        "pytorch": get_pytorch_info(),
        "nvidia_driver": get_nvidia_driver_info(),
        "ffprobe": check_ffprobe_availability()
        # Add other checks here if needed, e.g., nvcc for system-wide CUDA toolkit (developer info)
    }
    return summary

if __name__ == "__main__":
    print("--- System Compatibility Check ---")
    report = get_system_summary()

    print("\n[Python & OS]")
    print(f"  Python Version: {report['python']['python_version']}")
    print(f"  OS: {report['python']['operating_system']}")

    print("\n[PyTorch & CUDA]")
    if report['pytorch']['error_message']:
        print(f"  Error: {report['pytorch']['error_message']}")
    else:
        print(f"  PyTorch Installed: {'Yes' if report['pytorch']['installed'] else 'No'}")
        if report['pytorch']['installed']:
            print(f"  PyTorch Version: {report['pytorch']['version']}")
            print(f"  CUDA Available (via PyTorch): {'Yes' if report['pytorch']['cuda_available'] else 'No'}")
            if report['pytorch']['cuda_available']:
                print(f"    PyTorch CUDA Version: {report['pytorch']['cuda_version_pytorch']}")
                print(f"    GPU Count: {report['pytorch']['gpu_count']}")
                for i, gpu in enumerate(report['pytorch']['gpus']):
                    print(f"    GPU {i}: {gpu['name']}")
                    print(f"      Capability: {gpu['capability']}")
                    print(f"      Memory: {gpu['memory_mb']} MB")
            elif "cuda_status_message" in report['pytorch']:
                 print(f"    Status: {report['pytorch']['cuda_status_message']}")


    print("\n[NVIDIA Driver (from nvidia-smi)]")
    print(f"  Driver Version: {report['nvidia_driver']['driver_version']}")
    if report['nvidia_driver']['driver_version'] == "N/A":
         print(f"  Status: {report['nvidia_driver']['status_message']}")


    print("\n[FFprobe (for media duration)]")
    print(f"  Found: {'Yes' if report['ffprobe']['found'] else 'No'}")
    print(f"  Status: {report['ffprobe']['status_message']}")

    print("\n--- End of Check ---")

    # Example of how your loading screen might interpret this:
    print("\n--- Loading Screen Logic Example ---")
    can_run_gpu = False
    if report['pytorch']['installed'] and report['pytorch']['cuda_available']:
        can_run_gpu = True
        print("Primary Check: PyTorch with CUDA is available. GPU mode enabled.")
    else:
        print("Primary Check: PyTorch with CUDA NOT available. Application cannot use GPU.")
        if not report['pytorch']['installed']:
            print("  Reason: PyTorch not installed.")
        elif not report['pytorch']['cuda_available']:
            print("  Reason: PyTorch is CPU-only or CUDA initialization failed (check drivers).")


    ffprobe_critical = False # Set to True if your app cannot function without it
    if not report['ffprobe']['found']:
        print(f"Warning: FFprobe not found. {report['ffprobe']['status_message']}")
        if ffprobe_critical:
            print("  This is a critical component for this application.")
        else:
            print("  Progress bar accuracy and some media info might be affected.")
    else:
        print("FFprobe Check: OK.")