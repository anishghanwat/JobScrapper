"""
Setup script for Growth for Impact Job Listings Scraper
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.10 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("✗ Python 3.10 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def main():
    print("Growth for Impact - Job Listings Scraper Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("\nCreating virtual environment...")
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return False
    else:
        print("✓ Virtual environment already exists")
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Install Playwright browsers
    if not run_command("playwright install", "Installing Playwright browsers"):
        return False
    
    # Create sample data
    print("\nCreating sample data...")
    try:
        subprocess.run([sys.executable, "create_sample_data.py"], check=True)
        print("✓ Sample data created")
    except subprocess.CalledProcessError:
        print("✗ Failed to create sample data")
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate virtual environment:")
    print("   - Windows: venv\\Scripts\\activate")
    print("   - macOS/Linux: source venv/bin/activate")
    print("\n2. Test the scraper:")
    print("   python scraper.py --input sample_companies.xlsx --output results.xlsx --rows 3")
    print("\n3. Check the README.md for detailed usage instructions")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 