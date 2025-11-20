"""
Aria2c HuggingFace Downloader Node for ComfyUI
Downloads files from HuggingFace with multi-threaded aria2c support
Supports gated models with Bearer token authentication
"""

import os
import subprocess
import re
import shutil
import platform
import glob
import folder_paths
from comfy.cli_args import args

class Aria2cHuggingFaceDownloader:
    """
    Downloads files from HuggingFace repositories using aria2c for fast, 
    resumable multi-connection downloads. Supports private and gated models.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {
                    "multiline": False,
                    "default": "https://huggingface.co/username/repo/resolve/main/model.safetensors",
                    "placeholder": "Enter HuggingFace file URL"
                }),
                "save_path": (["models/checkpoints", "models/loras", "models/vae", "models/upscale_models", "models/clip", "models/controlnet", "custom"], {
                    "default": "models/checkpoints"
                }),
                "custom_path": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "Custom path (if save_path is 'custom')"
                }),
                "filename": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "Leave empty to use original filename"
                }),
                "connections": ("INT", {
                    "default": 16,
                    "min": 1,
                    "max": 16,
                    "step": 1,
                    "display": "number"
                }),
                "use_hf_token": ("BOOLEAN", {
                    "default": True
                }),
            },
            "optional": {
                "hf_token_override": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "Override token from settings"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_path",)
    FUNCTION = "download"
    CATEGORY = "loaders"
    OUTPUT_NODE = True
    
    def __init__(self):
        # Try to find aria2c executable (but don't fail if not found)
        self.aria2c_path = self._find_aria2c()
        
        if not self.aria2c_path:
            print("[Aria2c HF Downloader] Warning: aria2c not found. This node will not work until aria2c is installed.")
            print("[Aria2c HF Downloader] Please either:")
            print("[Aria2c HF Downloader]   1. Install aria2c system-wide, OR")
            print(f"[Aria2c HF Downloader]   2. Place aria2c in: {os.path.join(os.path.dirname(__file__), 'bin')}")
            print("[Aria2c HF Downloader] Alternatively, use the 'HF Downloader (Desktop Compatible)' node instead.")
    
    def _find_aria2c(self):
        """
        Find aria2c executable in PATH or local bin folder
        Returns the path to aria2c or None if not found
        """
        # First, check for bundled aria2c in node's bin folder
        node_dir = os.path.dirname(os.path.abspath(__file__))
        bin_dir = os.path.join(node_dir, "bin")
        
        # Detect platform and choose appropriate folder pattern
        system = platform.system().lower()
        arch = platform.machine().lower()
        
        # Search for aria2c in versioned folders
        if system == 'windows' or os.name == 'nt':
            # Look for Windows build folders (32bit or 64bit)
            if '64' in arch or 'amd64' in arch or 'x86_64' in arch:
                pattern = os.path.join(bin_dir, "aria2-*-win-64bit-build*", "aria2c.exe")
            else:
                pattern = os.path.join(bin_dir, "aria2-*-win-32bit-build*", "aria2c.exe")
            
            matches = glob.glob(pattern)
            if matches:
                bundled_aria2c = matches[0]  # Use first match
                print(f"[Aria2c HF Downloader] Using bundled aria2c: {bundled_aria2c}")
                return bundled_aria2c
            
            # Fallback to direct exe
            bundled_aria2c = os.path.join(bin_dir, "aria2c.exe")
            if os.path.exists(bundled_aria2c):
                print(f"[Aria2c HF Downloader] Using bundled aria2c: {bundled_aria2c}")
                return bundled_aria2c
                
        elif system == 'darwin':  # macOS
            # Look for macOS build folders
            pattern = os.path.join(bin_dir, "aria2-*-osx-*", "aria2c")
            matches = glob.glob(pattern)
            if not matches:
                pattern = os.path.join(bin_dir, "aria2-*-darwin-*", "aria2c")
                matches = glob.glob(pattern)
            if matches:
                bundled_aria2c = matches[0]
                try:
                    os.chmod(bundled_aria2c, 0o755)
                    # Verify it's executable
                    if not os.access(bundled_aria2c, os.X_OK):
                        print(f"[Aria2c HF Downloader] Warning: Could not make {bundled_aria2c} executable")
                        return None
                    print(f"[Aria2c HF Downloader] Using bundled aria2c: {bundled_aria2c}")
                    return bundled_aria2c
                except OSError as e:
                    print(f"[Aria2c HF Downloader] Error setting permissions: {e}")
                    return None
            
            # Fallback
            for name in ["aria2c-mac", "aria2c"]:
                bundled_aria2c = os.path.join(bin_dir, name)
                if os.path.exists(bundled_aria2c):
                    try:
                        os.chmod(bundled_aria2c, 0o755)
                        if not os.access(bundled_aria2c, os.X_OK):
                            print(f"[Aria2c HF Downloader] Warning: Could not make {bundled_aria2c} executable")
                            continue
                        print(f"[Aria2c HF Downloader] Using bundled aria2c: {bundled_aria2c}")
                        return bundled_aria2c
                    except OSError as e:
                        print(f"[Aria2c HF Downloader] Error setting permissions: {e}")
                        continue
                    
        else:  # Linux
            # Look for Linux build folders (including android builds which work on linux)
            pattern = os.path.join(bin_dir, "aria2-*-linux-*", "aria2c")
            matches = glob.glob(pattern)
            if not matches:
                # Try android builds as they also work on Linux
                pattern = os.path.join(bin_dir, "aria2-*-android-*", "aria2c")
                matches = glob.glob(pattern)
            if matches:
                bundled_aria2c = matches[0]
                try:
                    os.chmod(bundled_aria2c, 0o755)
                    # Verify it's executable
                    if not os.access(bundled_aria2c, os.X_OK):
                        print(f"[Aria2c HF Downloader] Warning: Could not make {bundled_aria2c} executable")
                        return None
                    print(f"[Aria2c HF Downloader] Using bundled aria2c: {bundled_aria2c}")
                    return bundled_aria2c
                except OSError as e:
                    print(f"[Aria2c HF Downloader] Error setting permissions: {e}")
                    return None
            
            # Fallback
            for name in ["aria2c-linux", "aria2c"]:
                bundled_aria2c = os.path.join(bin_dir, name)
                if os.path.exists(bundled_aria2c):
                    try:
                        os.chmod(bundled_aria2c, 0o755)
                        if not os.access(bundled_aria2c, os.X_OK):
                            print(f"[Aria2c HF Downloader] Warning: Could not make {bundled_aria2c} executable")
                            continue
                        print(f"[Aria2c HF Downloader] Using bundled aria2c: {bundled_aria2c}")
                        return bundled_aria2c
                    except OSError as e:
                        print(f"[Aria2c HF Downloader] Error setting permissions: {e}")
                        continue
        
        # Try system PATH
        try:
            result = subprocess.run(
                ["aria2c", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("[Aria2c HF Downloader] Using system aria2c from PATH")
                return "aria2c"
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
        
        return None
    
    def get_hf_token(self, hf_token_override):
        """
        Get HuggingFace token from override, settings, or environment
        """
        # Priority: override > settings > environment
        if hf_token_override and hf_token_override.strip():
            return hf_token_override.strip()
        
        # Try to get from ComfyUI settings (if implemented)
        # This would require extending ComfyUI settings system
        # For now, fallback to environment variable
        token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        
        return token
    
    def parse_filename_from_url(self, url):
        """
        Extract filename from HuggingFace URL
        """
        # HF URLs typically end with the filename after /resolve/main/ or /blob/main/
        match = re.search(r'/(?:resolve|blob)/[^/]+/(.+?)(?:\?|$)', url)
        if match:
            return match.group(1).split('/')[-1]
        
        # Fallback to last part of URL
        return url.split('/')[-1].split('?')[0]
    
    def get_full_path(self, save_path, custom_path, filename, url):
        """
        Construct full save path for downloaded file with path traversal protection
        """
        # Determine directory
        if save_path == "custom":
            if not custom_path:
                raise ValueError("Custom path must be specified when save_path is 'custom'")
            # Validate and normalize custom path
            directory = os.path.abspath(custom_path)
        else:
            # Get ComfyUI base path and append model folder
            base_path = folder_paths.base_path
            directory = os.path.abspath(os.path.join(base_path, save_path))
        
        # Determine filename and strip any path components (security)
        if not filename or not filename.strip():
            filename = self.parse_filename_from_url(url)
        
        # Security: Strip any path components from filename to prevent directory traversal
        filename = os.path.basename(filename)
        
        # Additional validation: ensure filename doesn't contain invalid characters
        if not filename or filename in ['.', '..']:
            raise ValueError(f"Invalid filename: {filename}")
        
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        return os.path.join(directory, filename)
    
    def download(self, url, save_path, custom_path, filename, connections, use_hf_token, hf_token_override=""):
        """
        Download file from HuggingFace using aria2c
        """
        # Check if aria2c is available
        if not self.aria2c_path:
            raise Exception(
                "aria2c is not installed or not found.\n\n"
                "Please either:\n"
                "1. Install aria2c system-wide (see README), OR\n"
                "2. Place aria2c in the 'bin' folder of this node, OR\n"
                "3. Use the 'HF Downloader (Desktop Compatible)' node instead (no aria2c required)"
            )
        
        # Validate URL
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        
        url = url.strip()
        
        # Validate HuggingFace URL
        if not ('huggingface.co' in url or 'hf.co' in url):
            print(f"[Aria2c HF Downloader] Warning: URL doesn't appear to be from HuggingFace: {url}")
        
        # Get full save path
        full_path = self.get_full_path(save_path, custom_path, filename, url)
        directory = os.path.dirname(full_path)
        filename_final = os.path.basename(full_path)
        
        # Check available disk space
        try:
            stat = shutil.disk_usage(directory)
            free_gb = stat.free / (1024**3)
            if stat.free < 1024 * 1024 * 1024:  # Less than 1GB free
                print(f"[Aria2c HF Downloader] ⚠ Warning: Low disk space ({free_gb:.2f} GB free)")
            else:
                print(f"[Aria2c HF Downloader] Available disk space: {free_gb:.2f} GB")
        except Exception as e:
            print(f"[Aria2c HF Downloader] Warning: Could not check disk space: {e}")
        
        # Get HuggingFace token
        hf_token = None
        if use_hf_token:
            hf_token = self.get_hf_token(hf_token_override)
        
        # Build aria2c command
        cmd = [
            self.aria2c_path,
            f"--dir={directory}",
            f"--out={filename_final}",
            f"--max-connection-per-server={connections}",
            f"--split={connections}",
            "--continue=true",
            "--min-split-size=1M",
            "--file-allocation=none",
            "--console-log-level=notice",
            "--summary-interval=5",
            "--retry-wait=3",
            "--max-tries=5",
            "--allow-overwrite=false",
            "--auto-file-renaming=true",
            url,  # URL should be last
        ]
        
        # Add authorization header for gated/private models
        if hf_token:
            # Don't store token in cmd list for logging purposes
            cmd.append(f"--header=Authorization: Bearer {hf_token}")
            print(f"[Aria2c HF Downloader] Using HuggingFace token for authentication")
        
        print(f"[Aria2c HF Downloader] Starting download...")
        print(f"[Aria2c HF Downloader] URL: {url}")
        print(f"[Aria2c HF Downloader] Destination: {full_path}")
        print(f"[Aria2c HF Downloader] Connections: {connections}")
        
        # Execute aria2c
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=None  # No timeout for large downloads
            )
            
            # Check result
            if result.returncode == 0:
                print(f"[Aria2c HF Downloader] ✓ Download completed successfully!")
                
                # Check if aria2c renamed the file (e.g., added .1, .2 suffix)
                actual_file = full_path
                if not os.path.exists(full_path):
                    # Look for files with numeric suffixes (e.g., filename.safetensors.1)
                    base_name = os.path.basename(full_path)
                    dir_path = os.path.dirname(full_path)
                    
                    # Check for numbered versions
                    for i in range(1, 100):  # Check up to .99
                        temp_file = os.path.join(dir_path, f"{base_name}.{i}")
                        if os.path.exists(temp_file):
                            print(f"[Aria2c HF Downloader] Found renamed file: {temp_file}")
                            print(f"[Aria2c HF Downloader] Renaming back to: {full_path}")
                            
                            # Rename the file back to the intended name using shutil for robustness
                            try:
                                shutil.move(temp_file, full_path)
                                actual_file = full_path
                                break
                            except (OSError, IOError) as rename_error:
                                print(f"[Aria2c HF Downloader] Warning: Could not rename file: {rename_error}")
                                actual_file = temp_file
                                break
                    else:
                        # File not found even with suffixes
                        print(f"[Aria2c HF Downloader] Warning: Expected file not found at {full_path}")
                        # List files in directory to help debug
                        try:
                            files_in_dir = os.listdir(dir_path)
                            matching_files = [f for f in files_in_dir if base_name in f]
                            if matching_files:
                                print(f"[Aria2c HF Downloader] Found similar files: {matching_files}")
                                actual_file = os.path.join(dir_path, matching_files[0])
                        except Exception:
                            pass
                
                # Clean up .aria2 control files
                try:
                    aria2_control = f"{actual_file}.aria2"
                    if os.path.exists(aria2_control):
                        os.remove(aria2_control)
                        print(f"[Aria2c HF Downloader] Cleaned up control file: {aria2_control}")
                except Exception as e:
                    print(f"[Aria2c HF Downloader] Note: Could not remove control file: {e}")
                
                print(f"[Aria2c HF Downloader] File saved to: {actual_file}")
                return (actual_file,)
            else:
                # Get error message but don't include full command (may contain token)
                error_msg = result.stderr if result.stderr else result.stdout
                print(f"[Aria2c HF Downloader] ✗ Download failed!")
                print(f"[Aria2c HF Downloader] Error: {error_msg}")
                raise Exception(f"aria2c download failed with code {result.returncode}. Check console for details.")
        
        except subprocess.TimeoutExpired:
            raise Exception("Download timed out (should not happen with timeout=None)")
        except Exception as e:
            # Don't log full command or details that might contain token
            raise Exception(f"Download error: {str(e)}")


# Node mappings
NODE_CLASS_MAPPINGS = {
    "Aria2cHuggingFaceDownloader": Aria2cHuggingFaceDownloader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Aria2cHuggingFaceDownloader": "Aria2c HF Downloader"
}
