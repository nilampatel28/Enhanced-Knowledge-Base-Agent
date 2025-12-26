"""Flask application factory for Enhanced Knowledge Base Agent API."""

from flask import Flask
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.agent import EnhancedKnowledgeBaseAgent
from enhanced_kb_agent.api.routes import register_routes


def create_app(config: KnowledgeBaseConfig = None) -> Flask:
    """Create and configure Flask application.
    
    Args:
        config: Knowledge base configuration. If None, uses default config.
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Initialize configuration
    if config is None:
        config = KnowledgeBaseConfig()
    
    app.config['KB_CONFIG'] = config
    
    # Initialize the agent
    agent = EnhancedKnowledgeBaseAgent(config)
    app.config['KB_AGENT'] = agent
    
    # Register routes
    register_routes(app)
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return {"error": "Bad request", "message": str(error)}, 400
    
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found", "message": str(error)}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error", "message": str(error)}, 500
    
    return app
