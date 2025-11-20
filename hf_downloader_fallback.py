"""
Fallback HuggingFace Downloader for ComfyUI-Desktop (No aria2c required)
Pure Python implementation that doesn't require subprocess calls
"""

import os
import urllib.request
import urllib.error
import folder_paths
from tqdm import tqdm

class HuggingFaceDownloaderFallback:
    """
    Downloads files from HuggingFace using pure Python (no subprocess).
    Compatible with ComfyUI-Desktop strict security mode.
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
    
    def download(self, url, save_path, custom_path, filename, use_hf_token, hf_token_override=""):
        """
        Download file from HuggingFace using pure Python urllib
        """
        try:
            # Determine save directory
            if save_path == "custom":
                if not custom_path:
                    raise ValueError("Custom path is required when save_path is 'custom'")
                save_dir = custom_path
            else:
                # Get ComfyUI base directory
                base_dir = folder_paths.base_path
                save_dir = os.path.join(base_dir, save_path)
            
            # Create directory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)
            
            # Determine filename
            if not filename:
                # Extract filename from URL
                filename = url.split('/')[-1].split('?')[0]
                if not filename:
                    filename = "downloaded_file"
            
            # Full output path
            output_file = os.path.join(save_dir, filename)
            
            print(f"[HF Downloader] Downloading: {url}")
            print(f"[HF Downloader] Saving to: {output_file}")
            
            # Prepare headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Add HuggingFace token if needed
            if use_hf_token:
                token = hf_token_override if hf_token_override else os.environ.get("HF_TOKEN", "")
                if token:
                    headers['Authorization'] = f'Bearer {token}'
                    print("[HF Downloader] Using HuggingFace token")
                else:
                    print("[HF Downloader] Warning: HF token requested but not found")
            
            # Create request
            req = urllib.request.Request(url, headers=headers)
            
            # Download with progress
            with urllib.request.urlopen(req) as response:
                total_size = int(response.headers.get('content-length', 0))
                
                with open(output_file, 'wb') as f:
                    if total_size:
                        # Download with progress bar
                        downloaded = 0
                        chunk_size = 8192
                        
                        print(f"[HF Downloader] File size: {total_size / (1024*1024):.2f} MB")
                        
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Print progress every 10MB
                            if downloaded % (10 * 1024 * 1024) < chunk_size:
                                progress = (downloaded / total_size) * 100
                                print(f"[HF Downloader] Progress: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)")
                    else:
                        # Download without progress
                        f.write(response.read())
            
            print(f"[HF Downloader] ✓ Download complete: {output_file}")
            return (output_file,)
            
        except urllib.error.HTTPError as e:
            if e.code == 403:
                error_msg = "403 Forbidden - Model may be gated. Enable 'use_hf_token' and provide a valid HuggingFace token."
            elif e.code == 404:
                error_msg = "404 Not Found - Check the URL is correct."
            else:
                error_msg = f"HTTP Error {e.code}: {e.reason}"
            
            print(f"[HF Downloader] ✗ Error: {error_msg}")
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            print(f"[HF Downloader] ✗ {error_msg}")
            raise Exception(error_msg)

NODE_CLASS_MAPPINGS = {
    "HuggingFaceDownloaderFallback": HuggingFaceDownloaderFallback
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HuggingFaceDownloaderFallback": "HF Downloader (Desktop Compatible)"
}
