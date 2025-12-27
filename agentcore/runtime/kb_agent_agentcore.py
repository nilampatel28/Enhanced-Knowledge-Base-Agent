"""
Enhanced Knowledge Base Agent - AgentCore Runtime Wrapper

This module wraps the Enhanced KB Agent for deployment on Amazon Bedrock AgentCore Runtime.
"""

import logging
import json

class EnhancedJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Enhanced KB Agent types."""
    def default(self, obj):
        # Handle enums
        if hasattr(obj, 'value'):
            return obj.value
        # Handle objects with __dict__
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        # Handle other types
        return str(obj)


def serialize_response(obj):
    """Recursively serialize objects to JSON-compatible format."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {k: serialize_response(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_response(item) for item in obj]
    elif hasattr(obj, 'value'):  # Enum
        return obj.value
    elif hasattr(obj, '__dict__'):
        return serialize_response(obj.__dict__)
    else:
        return str(obj)
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Add parent directory to path to find enhanced_kb_agent
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import AgentCore (will be available in AgentCore environment)
try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    AGENTCORE_AVAILABLE = True
except ImportError:
    AGENTCORE_AVAILABLE = False
    logger.warning("bedrock_agentcore not available - running in local mode")

# Import Enhanced KB Agent
try:
    from enhanced_kb_agent.agent import EnhancedKnowledgeBaseAgent
    from enhanced_kb_agent.config import KnowledgeBaseConfig
    KB_AGENT_AVAILABLE = True
except ImportError:
    KB_AGENT_AVAILABLE = False
    logger.warning("enhanced_kb_agent not available")

# Initialize AgentCore app if available
if AGENTCORE_AVAILABLE:
    app = BedrockAgentCoreApp()
else:
    app = None

# Initialize the Enhanced KB Agent
if KB_AGENT_AVAILABLE:
    try:
        config = KnowledgeBaseConfig()
        kb_agent = EnhancedKnowledgeBaseAgent(config)
        logger.info("✅ Enhanced KB Agent initialized")
    except Exception as e:
        logger.error(f"Failed to initialize KB Agent: {str(e)}")
        kb_agent = None
else:
    kb_agent = None


def format_response(status: str, data: Any, prompt: str = None, session_id: str = None) -> Dict:
    """Format response for AgentCore."""
    # Serialize data to JSON-compatible format
    serialized_data = serialize_response(data)
    
    return {
        "status": status,
        "data": serialized_data,
        "prompt": prompt,
        "session_id": session_id,
        "metadata": {
            "model": "enhanced-kb-agent",
            "version": "1.0.0",
            "framework": "strands-agents"
        }
    }


if AGENTCORE_AVAILABLE and app:
    @app.entrypoint
    async def invoke_agent(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for AgentCore runtime.
        
        Args:
            payload: Dictionary containing:
                - prompt: User query
                - context: Optional context
                - session_id: Optional session ID
        
        Returns:
            Agent response with results and metadata
        """
        try:
            # Extract parameters from payload
            prompt = payload.get("prompt")
            context = payload.get("context", {})
            session_id = payload.get("session_id")
            
            if not prompt:
                return format_response(
                    "error",
                    {"error": "No prompt provided"},
                    session_id=session_id
                )
            
            logger.info(f"Processing query: {prompt}")
            
            if not kb_agent:
                return format_response(
                    "error",
                    {"error": "KB Agent not initialized"},
                    prompt=prompt,
                    session_id=session_id
                )
            
            # Execute agent
            response = kb_agent.query(prompt)
            
            logger.info(f"Query completed successfully")
            
            return format_response(
                "success",
                response,
                prompt=prompt,
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return format_response(
                "error",
                {"error": str(e)},
                prompt=payload.get("prompt"),
                session_id=payload.get("session_id")
            )

    @app.entrypoint
    async def invoke_agent_streaming(payload: Dict[str, Any]):
        """
        Streaming version of agent invocation.
        
        Args:
            payload: Dictionary containing prompt and optional context
        
        Yields:
            Streaming response events
        """
        try:
            prompt = payload.get("prompt")
            session_id = payload.get("session_id")
            
            if not prompt:
                yield format_response(
                    "error",
                    {"error": "No prompt provided"},
                    session_id=session_id
                )
                return
            
            logger.info(f"Processing streaming query: {prompt}")
            
            if not kb_agent:
                yield format_response(
                    "error",
                    {"error": "KB Agent not initialized"},
                    prompt=prompt,
                    session_id=session_id
                )
                return
            
            # Stream response
            stream = kb_agent.stream(prompt)
            
            for event in stream:
                yield format_response(
                    "streaming",
                    event,
                    prompt=prompt,
                    session_id=session_id
                )
            
            logger.info(f"Streaming query completed")
            
        except Exception as e:
            logger.error(f"Error in streaming: {str(e)}")
            yield format_response(
                "error",
                {"error": str(e)},
                prompt=payload.get("prompt"),
                session_id=payload.get("session_id")
            )

    @app.entrypoint
    async def health_check(payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "enhanced-kb-agent",
            "version": "1.0.0",
            "kb_agent_available": kb_agent is not None
        }


# Local testing mode (when not running on AgentCore)
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8082, help='Port for local server')
    parser.add_argument('--local', action='store_true', help='Force local mode')
    args = parser.parse_args()
    
    # Use local mode if --local flag is set or if running with --port
    use_local_mode = args.local or '--port' in sys.argv
    
    if AGENTCORE_AVAILABLE and app and not use_local_mode:
        logger.info("Starting AgentCore runtime...")
        app.run()
    else:
        logger.info("Running in local mode (AgentCore not available or --local flag set)")
        
        # Simple local server for testing
        from flask import Flask, request, jsonify
        
        local_app = Flask(__name__)
        
        @local_app.route('/ping', methods=['GET'])
        def ping():
            return jsonify({"status": "Healthy"})
        
        @local_app.route('/invocations', methods=['POST'])
        def invocations():
            try:
                payload = request.get_json()
                prompt = payload.get("prompt")
                
                if not kb_agent:
                    return jsonify({"error": "KB Agent not initialized"}), 500
                
                response = kb_agent.query(prompt)
                formatted = format_response("success", response, prompt=prompt)
                
                # Use custom encoder for JSON serialization
                return local_app.response_class(
                    response=json.dumps(formatted, cls=EnhancedJSONEncoder),
                    status=200,
                    mimetype='application/json'
                )
            except Exception as e:
                logger.error(f"Error: {str(e)}", exc_info=True)
                return jsonify({"error": str(e)}), 500
        
        logger.info(f"Starting local Flask server on port {args.port}...")
        local_app.run(host='0.0.0.0', port=args.port, debug=False)
