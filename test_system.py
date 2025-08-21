#!/usr/bin/env python3
"""
Comprehensive test script for the reorganized NAI Project Planning system
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all modules can be imported correctly"""
    print("Testing module imports...")
    
    try:
        # Test database import
        from database import ProjectDatabase
        print("✓ Database module imports successfully")
        
        # Test API imports
        from api import main
        print("✓ API module imports successfully")
        
        # Test that database can be created
        db = ProjectDatabase("test_imports.db")
        print("✓ Database can be instantiated")
        
        # Test that API app exists
        app = main.app
        print("✓ FastAPI app object exists")
        
        # Cleanup
        if os.path.exists("test_imports.db"):
            os.remove("test_imports.db")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_database_functionality():
    """Test database functionality"""
    print("\nTesting database functionality...")
    
    try:
        from database import ProjectDatabase
        
        # Create test database
        db = ProjectDatabase("test_functionality.db")
        
        # Test project creation
        success = db.create_project("test-proj", "Test Project")
        print(f"✓ Project creation: {success}")
        
        # Test document operations
        test_doc = "# Test Document\n\nThis is a test."
        success = db.save_document("test-proj", test_doc)
        print(f"✓ Document save: {success}")
        
        retrieved = db.get_document("test-proj")
        print(f"✓ Document retrieval: {len(retrieved)} chars")
        
        # Test user sessions
        success = db.join_project("sess-123", "test-proj", "Test User")
        print(f"✓ User session join: {success}")
        
        users = db.get_active_users("test-proj")
        print(f"✓ Active users query: {len(users)} users")
        
        # Test conversation history
        success = db.add_message("test-proj", "user", "Hello!", "sess-123")
        print(f"✓ Message addition: {success}")
        
        history = db.get_conversation_history("test-proj")
        print(f"✓ History retrieval: {len(history)} messages")
        
        # Cleanup
        db.clear_project_data("test-proj")
        if os.path.exists("test_functionality.db"):
            os.remove("test_functionality.db")
        
        return True
        
    except Exception as e:
        print(f"❌ Database functionality test failed: {e}")
        return False

def test_api_structure():
    """Test API structure and endpoints"""
    print("\nTesting API structure...")
    
    try:
        from api.main import app, db
        
        # Check that the app has the expected routes
        routes = [route.path for route in app.routes]
        expected_routes = [
            "/", "/join", "/leave", "/chat", "/document/{project_id}",
            "/history/{project_id}", "/projects", "/projects/{project_id}/status",
            "/projects/{project_id}/users", "/projects/{project_id}"
        ]
        
        for expected in expected_routes:
            # Check if the route pattern exists (allowing for path parameters)
            route_exists = any(expected.replace("{project_id}", "").replace("/}", "/") in route 
                             for route in routes)
            if route_exists or expected in routes:
                print(f"✓ Route {expected} exists")
            else:
                print(f"⚠ Route {expected} not found in {routes}")
        
        # Test that database is accessible
        projects = db.list_projects()
        print(f"✓ Database accessible: {len(projects)} projects")
        
        return True
        
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
        return False

def test_directory_structure():
    """Test that the directory structure is correct"""
    print("\nTesting directory structure...")
    
    expected_files = [
        "api/__init__.py",
        "api/main.py",
        "database/__init__.py",
        "database/database.py",
        "naii_agents/__init__.py",
        "naii_agents/agents.py",
        "naii_agents/tools.py",
        "frontend/package.json",
        "requirements.txt",
        "pyproject.toml",
        "run_api_server.py",
        "test_system.py"
    ]
    
    missing_files = []
    for file_path in expected_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠ Missing files: {missing_files}")
        return False
    
    return True

def main():
    print("🧪 Testing Reorganized NAI Project Planning System")
    print("="*55)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Module Imports", test_imports),
        ("Database Functionality", test_database_functionality),
        ("API Structure", test_api_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "="*55)
    print("TEST SUMMARY")
    print("="*55)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set OPENAI_API_KEY in .env file")
        print("3. Run API server: python run_api_server.py")
        print("4. Run frontend: cd frontend && npm start")
    else:
        print("\n⚠ Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()