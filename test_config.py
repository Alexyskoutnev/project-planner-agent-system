#!/usr/bin/env python3
"""
Test script to verify local and production configuration for NAI Project Planner
"""
import os
import sys
from dotenv import load_dotenv

def test_configuration(env_type):
    print(f"\n=== Testing {env_type.upper()} Configuration ===")
    
    # Set environment
    os.environ['NODE_ENV'] = env_type
    
    # Load environment file
    if env_type == 'production':
        load_dotenv('.env.production')
    else:
        load_dotenv('.env')
    
    # Test environment-aware URLs (from main.py logic)
    ENVIRONMENT = os.getenv('NODE_ENV', 'development')
    if ENVIRONMENT == 'production':
        REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://naii-project-planner.naii.com/auth/duocallback')
        FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://naii-project-planner.naii.com')
        expected_cors_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000", 
            "http://127.0.0.1:8000",
            "https://naii-project-planner.naii.com",
            "http://172.28.3.20:8000",
            "http://172.28.3.20:3000"
        ]
    else:
        REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:8000/auth/duocallback')
        FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        expected_cors_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "http://localhost:8000",
            "http://127.0.0.1:8000"
        ]
    
    # Print configuration
    print(f"Environment: {ENVIRONMENT}")
    print(f"REDIRECT_URI: {REDIRECT_URI}")
    print(f"FRONTEND_URL: {FRONTEND_URL}")
    print(f"DUO_CLIENT_ID: {os.getenv('DUO_CLIENT_ID', 'NOT_SET')}")
    print(f"DUO_API_HOST: {os.getenv('DUO_API_HOST', 'NOT_SET')}")
    print(f"SESSION_SECRET: {'SET' if os.getenv('SESSION_SECRET') else 'NOT_SET'}")
    print(f"OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT_SET'}")
    print(f"Expected CORS Origins: {expected_cors_origins}")
    
    # Validate configuration
    errors = []
    
    if not os.getenv('DUO_CLIENT_ID'):
        errors.append("DUO_CLIENT_ID not set")
    if not os.getenv('DUO_SECRET'):
        errors.append("DUO_SECRET not set")
    if not os.getenv('DUO_API_HOST'):
        errors.append("DUO_API_HOST not set")
    if not os.getenv('OPENAI_API_KEY'):
        errors.append("OPENAI_API_KEY not set")
    if not os.getenv('SESSION_SECRET'):
        errors.append("SESSION_SECRET not set")
        
    if env_type == 'production':
        if 'naii-project-planner.naii.com' not in REDIRECT_URI:
            errors.append("Production REDIRECT_URI should contain production domain")
        if 'naii-project-planner.naii.com' not in FRONTEND_URL:
            errors.append("Production FRONTEND_URL should contain production domain")
    else:
        if 'localhost' not in REDIRECT_URI:
            errors.append("Development REDIRECT_URI should contain localhost")
        if 'localhost' not in FRONTEND_URL:
            errors.append("Development FRONTEND_URL should contain localhost")
    
    if errors:
        print(f"❌ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print(f"✅ {env_type.capitalize()} configuration is valid!")
        return True

def main():
    print("NAI Project Planner Configuration Test")
    print("=" * 50)
    
    # Test both configurations
    local_ok = test_configuration('development')
    prod_ok = test_configuration('production')
    
    print(f"\n=== Summary ===")
    print(f"Local Development: {'✅ PASS' if local_ok else '❌ FAIL'}")
    print(f"Production: {'✅ PASS' if prod_ok else '❌ FAIL'}")
    
    if local_ok and prod_ok:
        print("\n🎉 All configurations are ready for deployment!")
        return 0
    else:
        print("\n⚠️  Some configurations need attention.")
        return 1

if __name__ == '__main__':
    sys.exit(main())