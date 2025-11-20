# Bundled aria2c Binary

Place the aria2c executable here to bundle it with this node.

## Supported Naming Conventions

The node will automatically detect and use the correct binary for your platform:

### Windows
- `aria2c.exe`

### macOS
- `aria2c-mac` (preferred) or `aria2c`

### Linux
- `aria2c-linux` (preferred) or `aria2c`

## Download

Download the appropriate version for your platform from:
[https://github.com/aria2/aria2/releases](https://github.com/aria2/aria2/releases)

## Permissions (Linux/Mac)

The node will automatically set executable permissions, but you can also manually set them:

```bash
chmod +x aria2c
```

---

**Note**: If aria2c is already installed system-wide (in your PATH), you don't need to place anything here. The node will automatically detect and use the system installation.
