#!/usr/bin/env python3
"""
Hello Kitty BubbleTea TUI - Setup Script
========================================

Setup script for installing dependencies and configuring the project.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required!")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def create_virtual_environment():
    """Create a virtual environment for the project."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("📁 Virtual environment already exists!")
        return
    
    print("🐍 Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    print("✅ Virtual environment created!")


def install_dependencies():
    """Install project dependencies."""
    print("📦 Installing dependencies...")
    
    # Determine the correct pip path
    if os.name == "nt":  # Windows
        pip_path = "venv/Scripts/pip"
    else:  # Unix-like
        pip_path = "venv/bin/pip"
    
    # Install core dependencies
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    print("✅ Dependencies installed!")


def install_development_dependencies():
    """Install development dependencies."""
    print("🔧 Installing development dependencies...")
    
    if os.name == "nt":  # Windows
        pip_path = "venv/Scripts/pip"
    else:  # Unix-like
        pip_path = "venv/bin/pip"
    
    try:
        subprocess.run([pip_path, "install", "-r", "requirements-dev.txt"], check=True)
        print("✅ Development dependencies installed!")
    except subprocess.CalledProcessError:
        print("⚠️  Development dependencies installation failed (optional)")


def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = [
        "data",
        "logs", 
        "exports",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created!")


def setup_configuration():
    """Set up default configuration."""
    print("⚙️  Setting up configuration...")
    
    config_dir = Path.home() / ".hello_kitty_dashboard"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "config.yaml"
    if not config_file.exists():
        # Create default configuration
        default_config = """
# Hello Kitty BubbleTea TUI Configuration
theme: hello_kitty
enable_kawaii_mode: true
show_sparkles: true
show_hearts: true
color_profile: auto
refresh_interval: 5.0
enable_animations: true

# Shop Settings
shop_name: "🌸 Hello Kitty BubbleTea 🌸"
default_currency: "💝"
tax_rate: 0.088
loyalty_points_rate: 0.1

# Business Hours
business_hours_start: "10:00"
business_hours_end: "22:00"
timezone: "America/New_York"

# Notifications
enable_sound_notifications: false
show_order_notifications: true
show_inventory_alerts: true
notify_low_stock_threshold: 50

# Data Storage
auto_save: true
save_interval: 30.0

# Debug Settings
debug: false
log_level: "INFO"
"""
        
        with open(config_file, 'w') as f:
            f.write(default_config)
        
        print(f"✅ Default configuration created at {config_file}")


def create_desktop_shortcut():
    """Create a desktop shortcut (Linux/Mac)."""
    if os.name != "posix":
        return
    
    print("🔗 Creating desktop shortcut...")
    
    desktop_dir = Path.home() / "Desktop"
    if not desktop_dir.exists():
        return
    
    shortcut_path = desktop_dir / "HelloKittyBubbleTea.desktop"
    
    current_dir = Path.cwd()
    script_path = current_dir / "run.sh"
    
    shortcut_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Hello Kitty BubbleTea TUI
Comment=Kawaii bubble tea shop management system
Icon=applications-other
Exec={script_path.absolute()}
Terminal=true
Categories=Office;Finance;
"""
    
    with open(shortcut_path, 'w') as f:
        f.write(shortcut_content)
    
    # Make executable
    os.chmod(shortcut_path, 0o755)
    print("✅ Desktop shortcut created!")


def run_tests():
    """Run project tests."""
    print("🧪 Running tests...")
    
    if os.name == "nt":  # Windows
        python_path = "venv/Scripts/python"
    else:  # Unix-like
        python_path = "venv/bin/python"
    
    try:
        result = subprocess.run([python_path, "-m", "pytest", "tests/", "-v"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("⚠️  Some tests failed:")
            print(result.stdout)
            print(result.stderr)
    except subprocess.CalledProcessError:
        print("⚠️  Tests failed to run (pytest may not be installed)")


def main():
    """Main setup function."""
    print("🌸 Hello Kitty BubbleTea TUI Setup 🌸")
    print("=" * 50)
    
    try:
        check_python_version()
        create_virtual_environment()
        install_dependencies()
        install_development_dependencies()
        create_directories()
        setup_configuration()
        create_desktop_shortcut()
        run_tests()
        
        print("\n🎉 Setup completed successfully!")
        print("\nTo activate the virtual environment:")
        if os.name == "nt":
            print("  venv\\Scripts\\activate")
        else:
            print("  source venv/bin/activate")
        
        print("\nTo run the application:")
        if os.name == "nt":
            print("  .\\run.sh")
        else:
            print("  ./run.sh")
        
        print("\n🍵 Enjoy your kawaii bubble tea management experience! 🌸")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()