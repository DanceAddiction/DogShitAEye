#!/usr/bin/env python3
"""
Test script to verify Dog Walker Tracker components
"""
import sys
import os

def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    try:
        import database
        print("✓ database module imported")
        
        import frigate_client
        print("✓ frigate_client module imported")
        
        import tracker
        print("✓ tracker module imported")
        
        import analytics
        print("✓ analytics module imported")
        
        import main
        print("✓ main module imported")
        
        import web_interface
        print("✓ web_interface module imported")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\nTesting database initialization...")
    try:
        from database import init_database
        import tempfile
        
        # Use a temporary database for testing
        temp_db = os.path.join(tempfile.gettempdir(), 'test_tracker.db')
        
        engine, Session = init_database(temp_db)
        session = Session()
        
        # Try to create tables
        from database import Walker
        walker = Walker()
        session.add(walker)
        session.commit()
        
        print(f"✓ Database initialized successfully at {temp_db}")
        print(f"✓ Created test walker with ID: {walker.id}")
        
        session.close()
        
        # Clean up
        if os.path.exists(temp_db):
            os.remove(temp_db)
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    try:
        import yaml
        
        if not os.path.exists('config.yaml'):
            print("⚠ config.yaml not found, checking example...")
            if not os.path.exists('config.example.yaml'):
                print("✗ No configuration files found")
                return False
            else:
                print("✓ config.example.yaml found")
                with open('config.example.yaml', 'r') as f:
                    config = yaml.safe_load(f)
        else:
            print("✓ config.yaml found")
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
        
        # Verify required sections
        required_sections = ['frigate', 'cameras', 'database', 'images', 'tracking', 'analytics']
        for section in required_sections:
            if section not in config:
                print(f"✗ Missing required section: {section}")
                return False
            print(f"✓ Found section: {section}")
        
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\nChecking dependencies...")
    required = [
        'paho.mqtt.client',
        'requests',
        'cv2',
        'PIL',
        'sqlalchemy',
        'dateutil',
        'yaml',
        'flask'
    ]
    
    all_good = True
    for module_name in required:
        try:
            if module_name == 'cv2':
                import cv2
                print(f"✓ opencv-python installed (version {cv2.__version__})")
            elif module_name == 'PIL':
                import PIL
                print(f"✓ pillow installed (version {PIL.__version__})")
            elif module_name == 'yaml':
                import yaml
                print(f"✓ pyyaml installed")
            elif module_name == 'paho.mqtt.client':
                import paho.mqtt.client as mqtt
                print(f"✓ paho-mqtt installed")
            elif module_name == 'dateutil':
                import dateutil
                print(f"✓ python-dateutil installed")
            else:
                module = __import__(module_name)
                version = getattr(module, '__version__', 'unknown')
                print(f"✓ {module_name} installed (version {version})")
        except ImportError:
            print(f"✗ {module_name} not installed")
            all_good = False
    
    if not all_good:
        print("\n⚠ Install missing dependencies with: pip install -r requirements.txt")
    
    return all_good

def main():
    """Run all tests"""
    print("=" * 60)
    print("Dog Walker Tracker - System Test")
    print("=" * 60)
    
    tests = [
        ("Dependencies", check_dependencies),
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Configure config.yaml with your Frigate settings")
        print("2. Run: python main.py")
        print("3. Run: python web_interface.py (in another terminal)")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
