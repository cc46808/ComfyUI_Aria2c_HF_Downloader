# ComfyUI Aria2c HuggingFace Downloader

Fast, resumable multi-threaded downloads from HuggingFace using aria2c.

## Features

- ✅ **Fast multi-connection downloads** (up to 16 parallel connections)
- ✅ **Resume interrupted downloads** automatically
- ✅ **Support for gated/private models** with Bearer token authentication
- ✅ **Pre-configured save paths** for common model types
- ✅ **Custom save locations** supported
- ✅ **Progress tracking** in console
- ✅ **Bundled aria2c support** - works without system installation
- ✅ **Cross-platform** - Windows, Linux, macOS

## Installation

### Method 1: ComfyUI Manager (Recommended)

1. Open ComfyUI Manager
2. Search for "Aria2c HF Downloader"
3. Click Install
4. Restart ComfyUI

### Method 2: Manual Installation

1. Navigate to your ComfyUI custom_nodes folder:
   ```bash
   cd ComfyUI/custom_nodes
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ComfyUI_Aria2c_HF_Downloader.git
   ```

3. Restart ComfyUI

### Method 3: Direct Download

1. Download the repository as ZIP
2. Extract to `ComfyUI/custom_nodes/ComfyUI_Aria2c_HF_Downloader`
3. Restart ComfyUI

## Important: Security Settings

This node executes aria2c to download files. You need to adjust ComfyUI's security settings:

**Method 1: Start ComfyUI with local listen flag (Recommended)**
```bash
python main.py --listen 127.0.0.1
```

**Method 2: Lower security level in ComfyUI Manager**
- Open ComfyUI Manager settings
- Change security level to "normal" or lower
- Restart ComfyUI

See [ComfyUI Manager Security Policy](https://github.com/ltdrdata/ComfyUI-Manager#security-policy) for more details.

## aria2c Setup

The node will automatically detect aria2c from:
1. **Bundled version** in the `bin` folder (no installation needed!)
2. **System PATH** if aria2c is installed system-wide

### Option A: Use Bundled aria2c (Easiest for ComfyUI-Desktop)

Download aria2c for your platform and place it in the `bin` folder:

**Windows:**
1. Download from [aria2 releases](https://github.com/aria2/aria2/releases)
2. Extract `aria2-x.x.x-win-64bit-build1` folder
3. Place the entire folder in `ComfyUI/custom_nodes/ComfyUI_Aria2c_HF_Downloader/bin/`
4. The node will automatically find `aria2c.exe` inside

**Linux/macOS:**
1. Download the appropriate build from [aria2 releases](https://github.com/aria2/aria2/releases)
2. Extract the folder to `ComfyUI/custom_nodes/ComfyUI_Aria2c_HF_Downloader/bin/`
3. The node will automatically set executable permissions

### Option B: System-wide Installation

**Windows:**
```powershell
# Using Chocolatey
choco install aria2

# Or using Scoop
scoop install aria2
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install aria2

# Fedora
sudo dnf install aria2

# Arch
sudo pacman -S aria2
```

**macOS:**
```bash
brew install aria2
```

### Verify Installation
```bash
aria2c --version
```

## HuggingFace Token Setup

For gated or private models, you need a HuggingFace token.

### Method 1: Environment Variable (Recommended)
```bash
# Windows PowerShell
$env:HF_TOKEN="hf_your_token_here"

# Linux/macOS
export HF_TOKEN="hf_your_token_here"
```

### Method 2: Token Override
Enter your token directly in the node's `hf_token_override` field.

### Get Your Token
1. Go to https://huggingface.co/settings/tokens
2. Create a new token with "Read" permissions
3. Copy the token (starts with `hf_`)

## Usage

1. Add "Aria2c HF Downloader" node to your workflow
2. Enter the HuggingFace file URL (e.g., `https://huggingface.co/username/repo/resolve/main/model.safetensors`)
3. Select save location or use custom path
4. Set number of connections (16 recommended, max 32)
5. Enable "use_hf_token" for gated/private models
6. Run the workflow

## Example URLs

```
# Checkpoint
https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors

# LoRA
https://huggingface.co/username/lora-name/resolve/main/lora.safetensors

# VAE
https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors
```

## Troubleshooting

**"aria2c not found"** → Install aria2c and ensure it's in PATH

**"403 Forbidden"** → Model is gated, enable `use_hf_token` and provide valid token

**"Download failed"** → Check URL, internet connection, and disk space

## Installation Instructions

1. **Install aria2c** on your system (see above)
2. **Copy the folder** `comfyui_aria2c_hf_downloader` to `ComfyUI/custom_nodes/`
3. **Restart ComfyUI**
4. **Set HuggingFace token** (for gated models):
   ```bash
   # Windows PowerShell
   $env:HF_TOKEN="hf_your_token_here"
   
   # Linux/macOS
   export HF_TOKEN="hf_your_token_here"
   ```
5. **Use the node** from the "loaders" category

## Directory Structure

```
ComfyUI/custom_nodes/comfyui_aria2c_hf_downloader/
├── __init__.py
├── aria2c_hf_downloader.py
└── README.md
```

## How It Works

- **Bearer Token Authentication**: When `use_hf_token` is enabled, the node passes `--header="Authorization: Bearer YOUR_TOKEN"` to aria2c
- **Multi-connection Downloads**: aria2c splits the download into multiple parallel streams for maximum speed
- **Resumable**: If interrupted, aria2c automatically resumes from where it left off
- **ComfyUI Integration**: Follows ComfyUI custom node structure with proper INPUT_TYPES, RETURN_TYPES, and FUNCTION definitions

## License

MIT License

## Support

For issues or questions:
- Check aria2c installation: `aria2c --version`
- Verify HuggingFace token is valid
- Check ComfyUI console for detailed error messages
- Ensure sufficient disk space for downloads

## Credits

Created for ComfyUI community by integrating aria2c's powerful download capabilities with HuggingFace's model hub.