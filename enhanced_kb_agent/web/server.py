"""Web server for Enhanced Knowledge Base Agent."""

import os
import sys

# Add the project root to the Python path to handle module imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, send_from_directory, render_template_string
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.api import create_app


def create_web_app(config: KnowledgeBaseConfig = None) -> Flask:
    """Create Flask app with web UI and API.
    
    Args:
        config: Knowledge base configuration. If None, uses default config.
        
    Returns:
        Configured Flask application with web UI and API
    """
    app = create_app(config)
    
    # Get the directory where this file is located
    web_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(web_dir, 'static')
    
    # Serve static files
    @app.route('/')
    def index():
        """Serve the main HTML page."""
        try:
            return send_from_directory(static_dir, 'index.html')
        except Exception as e:
            # Fallback if file not found
            return f"<h1>Enhanced Knowledge Base Agent</h1><p>Error loading UI: {str(e)}</p>", 500
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files (CSS, JS, etc.)."""
        try:
            return send_from_directory(static_dir, filename)
        except Exception as e:
            return f"File not found: {filename}", 404
    
    return app


def run_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """Run the web server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Whether to run in debug mode
    """
    config = KnowledgeBaseConfig()
    app = create_web_app(config)
    
    print(f"Starting Enhanced Knowledge Base Agent Web Server")
    print(f"Access the web UI at http://localhost:{port}")
    print(f"API endpoints available at http://localhost:{port}/api")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Enhanced Knowledge Base Agent Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug)
