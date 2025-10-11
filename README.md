# Ghostty Build Script

A Python script to download, build, and install the [Ghostty](https://ghostty.org) terminal application on Fedora Linux.

## Usage

```bash
# Build and install Ghostty
./install.py

# Build using container (no local build dependencies required)
./install.py --container

# Build specific version
./install.py 1.1.5

# See all options
./install.py --help
```

## Requirements

- Python 3.13
- For local builds: Build dependencies from [Ghostty documentation](https://ghostty.org/docs/install/build#fedora)
- For container builds: `podman`
