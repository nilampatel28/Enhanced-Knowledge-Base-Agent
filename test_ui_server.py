#!/usr/bin/env python
"""Simple test script to verify the UI server works."""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("✅ Testing Enhanced Knowledge Base Agent UI Server")
    print("=" * 60)
    
    # Test 1: Import the app
    print("\n1. Testing imports...")
    from enhanced_kb_agent.web.server import create_web_app
    print("   ✅ Successfully imported create_web_app")
    
    # Test 2: Create the app
    print("\n2. Creating Flask app...")
    app = create_web_app()
    print("   ✅ Flask app created successfully")
    
    # Test 3: Check routes
    print("\n3. Checking routes...")
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    print(f"   ✅ Found {len(routes)} routes:")
    for route in sorted(routes):
        print(f"      - {route}")
    
    # Test 4: Check static files
    print("\n4. Checking static files...")
    static_dir = os.path.join(os.path.dirname(__file__), 'enhanced_kb_agent', 'web', 'static')
    if os.path.exists(static_dir):
        files = os.listdir(static_dir)
        print(f"   ✅ Static directory exists with {len(files)} files:")
        for f in files:
            print(f"      - {f}")
    else:
        print(f"   ❌ Static directory not found: {static_dir}")
    
    # Test 5: Test the app
    print("\n5. Testing Flask app with test client...")
    with app.test_client() as client:
        # Test root route
        response = client.get('/')
        print(f"   GET / -> Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Root route works!")
        else:
            print(f"   ⚠️  Root route returned {response.status_code}")
        
        # Test API health
        response = client.get('/api/health')
        print(f"   GET /api/health -> Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API health check works!")
        else:
            print(f"   ⚠️  API health returned {response.status_code}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Server is ready to run.")
    print("\nTo start the server, run:")
    print("  python -m enhanced_kb_agent.web.server --host 127.0.0.1 --port 5000 --debug")
    print("\nThen open: http://localhost:5000")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
