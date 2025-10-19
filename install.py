#!/usr/bin/env python3
"""
Ghostty Build Script

This script downloads, validates, and builds the Ghostty terminal application
using Zig as the build dependency.
"""

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


# Color codes for terminal output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"


def log_info(message: str) -> None:
    """Print info message with blue color."""
    print(f"{Colors.BLUE}[INFO]{Colors.END} {message}")


def log_success(message: str) -> None:
    """Print success message with green color."""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {message}")


def log_warning(message: str) -> None:
    """Print warning message with yellow color."""
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {message}")


def log_error(message: str) -> None:
    """Print error message with red color."""
    print(f"{Colors.RED}[ERROR]{Colors.END} {message}")


def download_file(url: str, destination: Path, pull_always: bool = False) -> None:
    """Download a file from URL to destination."""
    # Check if file already exists
    if destination.exists() and not pull_always:
        log_info(f"File {destination.name} already exists, skipping download")
        return

    log_info(f"Downloading {url} to {destination}")
    try:
        urllib.request.urlretrieve(url, destination)
        log_success(f"Downloaded {destination.name}")
    except Exception as e:
        log_error(f"Failed to download {url}: {e}")
        sys.exit(1)


def extract_tar_gz(archive_path: Path, extract_to: Path) -> None:
    """Extract a .tar.gz file to the specified directory."""
    log_info(f"Extracting {archive_path.name} to {extract_to}")
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(extract_to)
        log_success(f"Extracted {archive_path.name}")
    except Exception as e:
        log_error(f"Failed to extract {archive_path}: {e}")
        sys.exit(1)


def extract_tar_xz(archive_path: Path, extract_to: Path) -> None:
    """Extract a .tar.xz file to the specified directory."""
    log_info(f"Extracting {archive_path.name} to {extract_to}")
    try:
        with tarfile.open(archive_path, "r:xz") as tar:
            tar.extractall(extract_to)
        log_success(f"Extracted {archive_path.name}")
    except Exception as e:
        log_error(f"Failed to extract {archive_path}: {e}")
        sys.exit(1)


def extract_zip(archive_path: Path, extract_to: Path) -> None:
    """Extract a .zip file to the specified directory."""
    log_info(f"Extracting {archive_path.name} to {extract_to}")
    try:
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        log_success(f"Extracted {archive_path.name}")
    except Exception as e:
        log_error(f"Failed to extract {archive_path}: {e}")
        sys.exit(1)


def validate_signature(
    archive_path: Path, signature_path: Path, public_key: str
) -> bool:
    """Validate the archive signature using minisign."""
    log_info("Validating signature...")

    # Check if minisign is available
    try:
        subprocess.run(["minisign", "-v"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_error(
            "minisign is not installed. Please install it to validate signatures."
        )
        log_info("Install with: sudo dnf install minisign")
        sys.exit(1)

    try:
        # Create a temporary file for the public key
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".pub", delete=False
        ) as key_file:
            key_file.write(public_key)
            key_file_path = key_file.name

        # Debug: show the public key content
        log_info(f"Using public key: {public_key[:50]}...")

        # Validate the signature
        result = subprocess.run(
            ["minisign", "-V", "-p", key_file_path, "-m", str(archive_path)],
            capture_output=True,
            text=True,
        )

        # Clean up the temporary key file
        os.unlink(key_file_path)

        if result.returncode == 0:
            log_success("Signature validation passed")
            return True
        else:
            log_error(f"Signature validation failed: {result.stderr}")
            log_error(f"minisign stdout: {result.stdout}")
            return False

    except Exception as e:
        log_error(f"Error during signature validation: {e}")
        return False


def setup_zig(compiler_dir: Path, zig_version: str, pull_always: bool = False) -> None:
    """Download and setup Zig compiler if not already present."""
    zig_binary = compiler_dir / "zig"

    if zig_binary.exists() and not pull_always:
        log_info("Zig compiler already exists, skipping download")
        return

    log_info(f"Setting up Zig compiler version {zig_version}...")

    # Create compiler directory
    compiler_dir.mkdir(exist_ok=True)

    # Download Zig
    zig_url = f"https://ziglang.org/download/{zig_version}/zig-x86_64-linux-{zig_version}.tar.xz"
    zig_archive = compiler_dir / "zig.tar.xz"

    download_file(zig_url, zig_archive, pull_always)

    # Extract Zig
    extract_tar_xz(zig_archive, compiler_dir)
    # Move zig binary and lib directory to the correct location
    extracted_dir = compiler_dir / f"zig-x86_64-linux-{zig_version}"
    if extracted_dir.exists():
        # Move zig binary
        zig_src = extracted_dir / "zig"
        if zig_src.exists():
            zig_src.rename(zig_binary)

        # Move lib directory
        lib_src = extracted_dir / "lib"
        lib_dst = compiler_dir / "lib"
        if lib_src.exists():
            if lib_dst.exists():
                import shutil

                shutil.rmtree(lib_dst)
            lib_src.rename(lib_dst)

        # Clean up extracted directory
        import shutil

        shutil.rmtree(extracted_dir)

    # Clean up archive
    zig_archive.unlink()

    log_success("Zig compiler setup complete")


def build_ghostty(ghostty_dir: Path, compiler_dir: Path) -> None:
    """Build Ghostty using Zig."""
    log_info("Building Ghostty...")

    # Set up environment
    env = os.environ.copy()
    env["PATH"] = f"{compiler_dir}:{env.get('PATH', '')}"

    # Change to ghostty directory
    original_cwd = os.getcwd()
    os.chdir(ghostty_dir)

    try:
        # Run the build command
        result = subprocess.run(
            [
                "zig",
                "build",
                "-p",
                str(Path.home() / ".local"),
                "-Doptimize=ReleaseFast",
            ],
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            log_error("Build failed!")
            log_error(result.stderr)
            sys.exit(1)

        log_success("Build completed successfully")

    finally:
        os.chdir(original_cwd)


def install_desktop_file(ghostty_dir: Path) -> None:
    """Copy and configure the desktop files for Ghostty."""
    log_info("Installing desktop files...")

    # Install main application desktop file
    install_app_desktop_file(ghostty_dir)

    # Install KDE Dolphin service menu desktop file
    install_dolphin_desktop_file(ghostty_dir)


def install_app_desktop_file(ghostty_dir: Path) -> None:
    """Install the main application desktop file."""
    log_info("Installing application desktop file...")

    # Source desktop file
    source_desktop = ghostty_dir / "dist" / "linux" / "app.desktop.in"
    if not source_desktop.exists():
        log_error(f"Desktop file not found at {source_desktop}")
        return

    # Destination directory
    applications_dir = Path.home() / ".local" / "share" / "applications"
    applications_dir.mkdir(parents=True, exist_ok=True)

    # Destination file
    dest_desktop = applications_dir / "ghostty.desktop"

    try:
        # Read source file
        with open(source_desktop, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace placeholders
        ghostty_path = str(Path.home() / ".local" / "bin" / "ghostty")
        content = content.replace("@GHOSTTY@", ghostty_path)
        content = content.replace("@NAME@", "Ghostty")
        content = content.replace("@APPID@", "com.mitchellh.ghostty")

        # Write to destination
        with open(dest_desktop, "w", encoding="utf-8") as f:
            f.write(content)

        log_success(f"Application desktop file installed to {dest_desktop}")

    except Exception as e:
        log_error(f"Failed to install application desktop file: {e}")


def install_dolphin_desktop_file(ghostty_dir: Path) -> None:
    """Install the KDE Dolphin service menu desktop file."""
    log_info("Installing Dolphin service menu desktop file...")

    # Source desktop file
    source_desktop = ghostty_dir / "dist" / "linux" / "ghostty_dolphin.desktop"
    if not source_desktop.exists():
        log_error(f"Dolphin desktop file not found at {source_desktop}")
        return

    # Destination directory
    kio_dir = Path.home() / ".local" / "share" / "kio" / "servicemenus"
    kio_dir.mkdir(parents=True, exist_ok=True)

    # Destination file
    dest_desktop = kio_dir / "com.mitchellh.ghostty.desktop"

    try:
        # Copy file without modifications
        import shutil

        shutil.copy2(source_desktop, dest_desktop)

        log_success(f"Dolphin service menu desktop file installed to {dest_desktop}")

    except Exception as e:
        log_error(f"Failed to install Dolphin service menu desktop file: {e}")


def uninstall_ghostty() -> None:
    """Remove all installed Ghostty artifacts."""
    log_info("Uninstalling Ghostty...")

    removed_items = []
    failed_items = []

    # Remove binary
    ghostty_binary = Path.home() / ".local" / "bin" / "ghostty"
    if ghostty_binary.exists():
        try:
            ghostty_binary.unlink()
            removed_items.append(f"Binary: {ghostty_binary}")
            log_success(f"Removed binary: {ghostty_binary}")
        except Exception as e:
            failed_items.append(f"Binary: {ghostty_binary} ({e})")
            log_error(f"Failed to remove binary {ghostty_binary}: {e}")
    else:
        log_info("Binary not found, skipping removal")

    # Remove application desktop file
    app_desktop = Path.home() / ".local" / "share" / "applications" / "ghostty.desktop"
    if app_desktop.exists():
        try:
            app_desktop.unlink()
            removed_items.append(f"Application desktop file: {app_desktop}")
            log_success(f"Removed application desktop file: {app_desktop}")
        except Exception as e:
            failed_items.append(f"Application desktop file: {app_desktop} ({e})")
            log_error(f"Failed to remove application desktop file {app_desktop}: {e}")
    else:
        log_info("Application desktop file not found, skipping removal")

    # Remove Dolphin service menu desktop file
    dolphin_desktop = (
        Path.home()
        / ".local"
        / "share"
        / "kio"
        / "servicemenus"
        / "com.mitchellh.ghostty.desktop"
    )
    if dolphin_desktop.exists():
        try:
            dolphin_desktop.unlink()
            removed_items.append(f"Dolphin service menu: {dolphin_desktop}")
            log_success(f"Removed Dolphin service menu: {dolphin_desktop}")
        except Exception as e:
            failed_items.append(f"Dolphin service menu: {dolphin_desktop} ({e})")
            log_error(f"Failed to remove Dolphin service menu {dolphin_desktop}: {e}")
    else:
        log_info("Dolphin service menu not found, skipping removal")

    # Summary
    if removed_items:
        log_success(f"Successfully removed {len(removed_items)} items:")
        for item in removed_items:
            log_info(f"  - {item}")

    if failed_items:
        log_error(f"Failed to remove {len(failed_items)} items:")
        for item in failed_items:
            log_error(f"  - {item}")
        sys.exit(1)

    if not removed_items and not failed_items:
        log_warning("No Ghostty artifacts found to remove")
    else:
        log_success("Ghostty uninstallation completed successfully")


def verify_build() -> bool:
    """Verify that the build artifacts are in $HOME/.local."""
    local_dir = Path.home() / ".local"
    bin_dir = local_dir / "bin"

    log_info("Verifying build artifacts...")

    # Check if ghostty binary exists
    ghostty_binary = bin_dir / "ghostty"
    if ghostty_binary.exists():
        log_success(f"Ghostty binary found at {ghostty_binary}")
        return True
    else:
        log_error(f"Ghostty binary not found at {ghostty_binary}")
        return False


def check_podman() -> bool:
    """Check if podman is available."""
    try:
        subprocess.run(
            ["podman", "--version"], capture_output=True, check=True, text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_error("podman is not installed. Please install it to use --container")
        log_info("Install with: sudo dnf install podman")
        return False


def extract_artifacts_from_container(
    container_name: str, version: str, temp_dir: Path
) -> tuple[Path, Path]:
    """Extract binary and desktop files from container.

    Returns: (binary_path, dist_dir_path)
    """
    log_info("Extracting binary from container...")

    # Extract binary
    binary_path = temp_dir / "ghostty"
    result = subprocess.run(
        [
            "podman",
            "cp",
            f"{container_name}:/build/output/bin/ghostty",
            str(binary_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        log_error(f"Failed to extract binary from container: {result.stderr}")
        raise RuntimeError("Binary extraction failed")

    log_success("Binary extracted successfully")

    # Extract desktop files
    log_info("Extracting desktop files from container...")
    dist_dir = temp_dir / "dist"
    result = subprocess.run(
        [
            "podman",
            "cp",
            f"{container_name}:/build/ghostty-{version}/dist",
            str(dist_dir),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        log_error(f"Failed to extract desktop files from container: {result.stderr}")
        raise RuntimeError("Desktop files extraction failed")

    log_success("Desktop files extracted successfully")

    return binary_path, dist_dir


def build_ghostty_container(
    version: str, zig_version: str, no_cache: bool
) -> None:
    """Build Ghostty using container and install artifacts."""
    import shutil
    import random
    import string

    # Check if podman is available
    if not check_podman():
        sys.exit(1)

    # Check if Containerfile exists
    containerfile = Path.cwd() / "Containerfile"
    if not containerfile.exists():
        log_error(f"Containerfile not found at {containerfile}")
        log_error("Please ensure Containerfile is in the current directory")
        sys.exit(1)

    log_info(f"Building Ghostty {version} using container with Zig {zig_version}...")

    # Build container image
    build_cmd = [
        "podman",
        "build",
        "-t",
        f"ghostty-builder:{version}",
        "--build-arg",
        f"GHOSTTY_VERSION={version}",
        "--build-arg",
        f"ZIG_VERSION={zig_version}",
        "-f",
        "Containerfile",
        ".",
    ]

    if no_cache:
        build_cmd.insert(2, "--no-cache")

    log_info("Building container image (this may take a few minutes)...")
    result = subprocess.run(build_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        log_error("Container build failed!")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        sys.exit(1)

    log_success("Container image built successfully")

    # Generate random suffix for container name
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    container_name = f"ghostty-extract-{random_suffix}"

    # Create temporary directory for extraction
    temp_dir = Path(tempfile.mkdtemp(prefix="ghostty-container-"))

    try:
        # Create container instance
        log_info("Creating temporary container for artifact extraction...")
        result = subprocess.run(
            [
                "podman",
                "create",
                "--name",
                container_name,
                f"ghostty-builder:{version}",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            log_error(f"Failed to create container: {result.stderr}")
            sys.exit(1)

        try:
            # Extract artifacts
            binary_path, dist_dir = extract_artifacts_from_container(
                container_name, version, temp_dir
            )

            # Install binary
            log_info("Installing binary to ~/.local/bin...")
            bin_dir = Path.home() / ".local" / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)

            dest_binary = bin_dir / "ghostty"
            shutil.copy2(binary_path, dest_binary)
            dest_binary.chmod(0o755)  # Make executable

            log_success(f"Binary installed to {dest_binary}")

            # Install desktop files
            log_info("Installing desktop files...")
            # Create a temporary ghostty directory structure for install_desktop_file
            ghostty_temp_dir = temp_dir / "ghostty-source"
            ghostty_temp_dir.mkdir(exist_ok=True)
            shutil.move(str(dist_dir), str(ghostty_temp_dir / "dist"))

            install_desktop_file(ghostty_temp_dir)

        finally:
            # Remove container
            log_info("Cleaning up container...")
            subprocess.run(
                ["podman", "rm", container_name],
                capture_output=True,
            )
            log_success("Container removed")

    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    # Verify installation
    if verify_build():
        log_success("Container build verification passed!")
        log_info("Ghostty has been successfully built and installed to $HOME/.local")
    else:
        log_error("Container build verification failed!")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Build Ghostty terminal application",
        epilog="""
Examples:
  %(prog)s                           # Build latest Ghostty (1.2.0)
  %(prog)s 1.1.5                     # Build specific version
  %(prog)s --uninstall               # Remove all installed Ghostty artifacts
  %(prog)s --container               # Build using container (requires podman)
  %(prog)s --container --zig-version 0.13.0  # Container build with custom Zig version
  %(prog)s --skip-build              # Only download and extract source
  %(prog)s --pull-always             # Force re-download all files
  %(prog)s --skip-signature          # Skip signature validation
  %(prog)s 1.2.0 --skip-build --pull-always  # Combine options

The script downloads Ghostty source code, validates signatures, sets up Zig compiler,
builds Ghostty, and installs it to $HOME/.local/bin. Use --uninstall to remove all
installed artifacts. Use --container to build in a container without installing build
dependencies locally.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "version",
        nargs="?",
        default="1.2.0",
        help="Ghostty version to build (default: %(default)s)",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove all installed Ghostty artifacts (binary and desktop files)",
    )
    parser.add_argument(
        "--container",
        action="store_true",
        help="Build Ghostty using container (requires podman)",
    )
    parser.add_argument(
        "--zig-version",
        default="0.14.1",
        help="Zig compiler version to use (default: %(default)s)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force container rebuild without cache (only used with --container)",
    )
    parser.add_argument(
        "--pull-always",
        action="store_true",
        help="Always download files even if they already exist in the current directory",
    )
    parser.add_argument(
        "--skip-signature",
        action="store_true",
        help="Skip signature validation (not recommended for security)",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip build and installation steps (only download and extract source code)",
    )

    args = parser.parse_args()
    version = args.version
    uninstall = args.uninstall
    container = args.container
    zig_version = args.zig_version
    no_cache = args.no_cache
    pull_always = args.pull_always
    skip_signature = args.skip_signature
    skip_build = args.skip_build

    # Handle uninstall flag precedence - takes precedence over all other flags
    if uninstall:
        uninstall_ghostty()
        return

    # Handle container build
    if container:
        # Log warnings for ignored flags
        if skip_build:
            log_warning("--skip-build ignored when using --container")
        if skip_signature:
            log_warning(
                "--skip-signature ignored when using --container (signature always verified)"
            )
        if pull_always:
            log_warning(
                "--pull-always ignored when using --container (always downloads fresh)"
            )
        if no_cache:
            log_info("Using --no-cache: container will be rebuilt without cache")

        # Execute container workflow
        build_ghostty_container(version, zig_version, no_cache)
        return

    log_info(f"Building Ghostty version {version}")

    # Public key for signature validation
    public_key = "untrusted comment: minisign public key 0x23149WL2sEpT\nRWQlAjJC23149WL2sEpT/l0QKy7hMIFhYdQOFy0Z7z7PbneUgvlsnYcV"

    # Download files to current working directory
    # Download Ghostty release
    ghostty_url = (
        f"https://release.files.ghostty.org/{version}/ghostty-{version}.tar.gz"
    )
    ghostty_archive = Path.cwd() / f"ghostty-{version}.tar.gz"
    download_file(ghostty_url, ghostty_archive, pull_always)

    # Download signature
    signature_url = (
        f"https://release.files.ghostty.org/{version}/ghostty-{version}.tar.gz.minisig"
    )
    signature_file = Path.cwd() / f"ghostty-{version}.tar.gz.minisig"
    download_file(signature_url, signature_file, pull_always)

    # Validate signature
    if skip_signature:
        log_warning("Skipping signature validation (not recommended)")
    else:
        if not validate_signature(ghostty_archive, signature_file, public_key):
            log_error("Signature validation failed, aborting build")
            sys.exit(1)

    # Extract Ghostty
    ghostty_dir = Path.cwd() / f"ghostty-{version}"
    if ghostty_dir.exists():
        import shutil

        shutil.rmtree(ghostty_dir)

    extract_tar_gz(ghostty_archive, Path.cwd())

    if skip_build:
        log_info("Skipping build and installation steps")
        log_success(f"Ghostty source code extracted to {ghostty_dir}")
        log_info("Use the script without --skip-build to build and install Ghostty")
    else:
        # Setup Zig compiler
        compiler_dir = Path.cwd() / "compiler"
        setup_zig(compiler_dir, zig_version, pull_always)

        # Build Ghostty
        build_ghostty(ghostty_dir, compiler_dir)

        # Install desktop file
        install_desktop_file(ghostty_dir)

        # Verify build
        if verify_build():
            log_success("Build verification passed!")
            log_info(
                "Ghostty has been successfully built and installed to $HOME/.local"
            )
        else:
            log_error("Build verification failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()
