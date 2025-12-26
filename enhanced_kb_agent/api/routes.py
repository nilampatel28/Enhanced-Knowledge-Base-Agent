"""API routes for Enhanced Knowledge Base Agent."""

from flask import Blueprint, request, jsonify, current_app
from enhanced_kb_agent.types import ContentType
import json
from datetime import datetime


def register_routes(app):
    """Register all API routes.
    
    Args:
        app: Flask application instance
    """
    
    # Query endpoints
    @app.route('/api/query', methods=['POST'])
    def query():
        """Execute a complex query.
        
        Request body:
        {
            "query": "What is the relationship between X and Y?"
        }
        
        Returns:
            {
                "query": "...",
                "answer": "...",
                "sources": [...],
                "confidence": 0.95,
                "reasoning_steps": [...]
            }
        """
        try:
            data = request.get_json()
            if not data or 'query' not in data:
                return {"error": "Missing 'query' field"}, 400
            
            query_text = data['query']
            agent = current_app.config['KB_AGENT']
            
            result = agent.query(query_text)
            
            # Convert result to JSON-serializable format
            response = {
                "query": result.original_query,
                "answer": result.answer,
                "sources": result.sources,
                "confidence": result.confidence,
                "reasoning_steps": [
                    {
                        "step_number": step.step_number,
                        "query": step.query.sub_query_text,
                        "results_count": len(step.results),
                        "execution_time_ms": step.execution_time_ms,
                        "success": step.success,
                        "error_message": step.error_message
                    }
                    for step in result.reasoning_steps
                ],
                "conflicts_detected": result.conflicts_detected
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            return {"error": str(e)}, 500
    
    # Storage endpoints
    @app.route('/api/store', methods=['POST'])
    def store():
        """Store new information in the knowledge base.
        
        Request body:
        {
            "content": "...",
            "content_type": "text/plain",
            "metadata": {
                "title": "...",
                "description": "...",
                "tags": [...],
                "categories": [...],
                "source": "..."
            }
        }
        
        Returns:
            {
                "content_id": "...",
                "version": 1,
                "created_at": "...",
                "message": "Content stored successfully"
            }
        """
        try:
            data = request.get_json()
            if not data or 'content' not in data:
                return {"error": "Missing 'content' field"}, 400
            
            content = data['content']
            content_type = data.get('content_type', 'text/plain')
            metadata = data.get('metadata', {})
            
            agent = current_app.config['KB_AGENT']
            
            content_id = agent.store(content, metadata)
            
            response = {
                "content_id": content_id,
                "version": 1,
                "created_at": datetime.now().isoformat(),
                "message": "Content stored successfully"
            }
            
            return jsonify(response), 201
        
        except Exception as e:
            return {"error": str(e)}, 500
    
    # Update endpoints
    @app.route('/api/update/<content_id>', methods=['PUT'])
    def update(content_id):
        """Update existing information.
        
        Request body:
        {
            "content": "...",
            "change_reason": "..."
        }
        
        Returns:
            {
                "content_id": "...",
                "version": 2,
                "updated_at": "...",
                "message": "Content updated successfully"
            }
        """
        try:
            data = request.get_json()
            if not data or 'content' not in data:
                return {"error": "Missing 'content' field"}, 400
            
            new_content = data['content']
            change_reason = data.get('change_reason', 'Updated via API')
            
            agent = current_app.config['KB_AGENT']
            
            result = agent.update(content_id, new_content, change_reason)
            
            response = {
                "content_id": content_id,
                "version": 2,
                "updated_at": datetime.now().isoformat(),
                "message": "Content updated successfully"
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            return {"error": str(e)}, 500
    
    # Version history endpoints
    @app.route('/api/versions/<content_id>', methods=['GET'])
    def get_versions(content_id):
        """Retrieve version history for content.
        
        Query parameters:
        - limit: Maximum number of versions to return (default: 10)
        - offset: Number of versions to skip (default: 0)
        
        Returns:
            {
                "content_id": "...",
                "versions": [
                    {
                        "version_number": 1,
                        "created_at": "...",
                        "changed_by": "...",
                        "change_reason": "..."
                    },
                    ...
                ],
                "total_versions": 5
            }
        """
        try:
            limit = request.args.get('limit', 10, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            agent = current_app.config['KB_AGENT']
            
            versions = agent.information_manager.get_version_history(content_id)
            
            # Apply pagination
            paginated_versions = versions[offset:offset + limit]
            
            response = {
                "content_id": content_id,
                "versions": [
                    {
                        "version_number": v.version_number,
                        "created_at": v.changed_at.isoformat(),
                        "changed_by": v.changed_by,
                        "change_reason": v.change_reason
                    }
                    for v in paginated_versions
                ],
                "total_versions": len(versions),
                "returned_versions": len(paginated_versions)
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            return {"error": str(e)}, 500
    
    # Category management endpoints
    @app.route('/api/categories', methods=['GET'])
    def get_categories():
        """Retrieve all categories.
        
        Returns:
            {
                "categories": [
                    {
                        "id": "...",
                        "name": "...",
                        "description": "...",
                        "content_count": 5
                    },
                    ...
                ]
            }
        """
        try:
            agent = current_app.config['KB_AGENT']
            
            categories = agent.knowledge_organizer.get_all_categories()
            
            response = {
                "categories": [
                    {
                        "id": cat.id,
                        "name": cat.name,
                        "description": cat.description,
                        "content_count": cat.content_count
                    }
                    for cat in categories
                ]
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            return {"error": str(e)}, 500
    
    @app.route('/api/categories', methods=['POST'])
    def create_category():
        """Create a new category.
        
        Request body:
        {
            "name": "...",
            "description": "...",
            "parent_category": "..." (optional)
        }
        
        Returns:
            {
                "id": "...",
                "name": "...",
                "message": "Category created successfully"
            }
        """
        try:
            data = request.get_json()
            if not data or 'name' not in data:
                return {"error": "Missing 'name' field"}, 400
            
            agent = current_app.config['KB_AGENT']
            
            category_id = agent.knowledge_organizer.create_category(
                name=data['name'],
                description=data.get('description', ''),
                parent_category=data.get('parent_category')
            )
            
            response = {
                "id": category_id,
                "name": data['name'],
                "message": "Category created successfully"
            }
            
            return jsonify(response), 201
        
        except Exception as e:
            return {"error": str(e)}, 500
    
    # Tag management endpoints
    @app.route('/api/tags', methods=['GET'])
    def get_tags():
        """Retrieve all tags.
        
        Returns:
            {
                "tags": [
                    {
                        "id": "...",
                        "name": "...",
                        "usage_count": 10
                    },
                    ...
                ]
            }
        """
        try:
            agent = current_app.config['KB_AGENT']
            
            tags = agent.knowledge_organizer.get_all_tags()
            
            response = {
                "tags": [
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "usage_count": tag.usage_count
                    }
                    for tag in tags
                ]
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            return {"error": str(e)}, 500
    
    # Search endpoints
    @app.route('/api/search', methods=['POST'])
    def search():
        """Search for content by tags or categories.
        
        Request body:
        {
            "tags": [...] (optional),
            "categories": [...] (optional),
            "query": "..." (optional)
        }
        
        Returns:
            {
                "results": [
                    {
                        "content_id": "...",
                        "title": "...",
                        "relevance": 0.95
                    },
                    ...
                ],
                "total_results": 5
            }
        """
        try:
            data = request.get_json()
            
            tags = data.get('tags', [])
            categories = data.get('categories', [])
            query_text = data.get('query')
            
            agent = current_app.config['KB_AGENT']
            
            results = []
            
            if tags:
                # Convert tag names to tag IDs
                all_tags = agent.knowledge_organizer.get_all_tags()
                tag_name_to_id = {tag.name: tag.id for tag in all_tags}
                tag_ids = [tag_name_to_id.get(tag) for tag in tags if tag in tag_name_to_id]
                
                if tag_ids:
                    tag_results = agent.knowledge_organizer.search_by_tags(tag_ids)
                    results.extend(tag_results)
            
            if categories:
                # Convert category names to category IDs
                all_categories = agent.knowledge_organizer.get_all_categories()
                cat_name_to_id = {cat.name: cat.id for cat in all_categories}
                category_ids = [cat_name_to_id.get(cat) for cat in categories if cat in cat_name_to_id]
                
                if category_ids:
                    category_results = agent.knowledge_organizer.search_by_categories(category_ids)
                    results.extend(category_results)
            
            if query_text:
                query_results = agent.query(query_text)
                results.append({
                    "content_id": "query_result",
                    "title": query_results.answer[:100],
                    "relevance": query_results.confidence
                })
            
            # Remove duplicates
            seen = set()
            unique_results = []
            for r in results:
                if isinstance(r, str):
                    # If result is a content_id string, convert to dict
                    r = {"content_id": r, "title": "", "relevance": 0.0}
                if r.get('content_id') not in seen:
                    seen.add(r.get('content_id'))
                    unique_results.append(r)
            
            response = {
                "results": unique_results,
                "total_results": len(unique_results)
            }
            
            return jsonify(response), 200
        
        except Exception as e:
            return {"error": str(e)}, 500
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health():
        """Health check endpoint.
        
        Returns:
            {
                "status": "healthy",
                "timestamp": "..."
            }
        """
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }), 200
    
    # Configuration endpoint
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """Get current configuration.
        
        Returns:
            Configuration dictionary
        """
        try:
            config = current_app.config['KB_CONFIG']
            return jsonify(config.to_dict()), 200
        except Exception as e:
            return {"error": str(e)}, 500
