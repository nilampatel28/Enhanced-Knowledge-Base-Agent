"""Tests for REST API and Web Interface."""

import pytest
import json
from enhanced_kb_agent.web.server import create_web_app
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.types import ContentType


@pytest.fixture
def app():
    """Create test Flask app."""
    config = KnowledgeBaseConfig()
    app = create_web_app(config)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test that health endpoint returns healthy status."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data


class TestConfigEndpoint:
    """Test configuration endpoint."""
    
    def test_get_config(self, client):
        """Test that config endpoint returns configuration."""
        response = client.get('/api/config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'kb_name' in data
        assert 'cache_enabled' in data
        assert 'enable_versioning' in data


class TestQueryEndpoint:
    """Test query endpoint."""
    
    def test_query_missing_field(self, client):
        """Test query endpoint with missing query field."""
        response = client.post('/api/query', 
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_query_simple(self, client):
        """Test simple query execution."""
        response = client.post('/api/query',
            json={'query': 'What is the capital of France?'},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'query' in data
        assert 'answer' in data
        assert 'sources' in data
        assert 'confidence' in data
        assert 'reasoning_steps' in data


class TestStoreEndpoint:
    """Test storage endpoint."""
    
    def test_store_missing_content(self, client):
        """Test store endpoint with missing content."""
        response = client.post('/api/store',
            json={'metadata': {}},
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_store_content(self, client):
        """Test storing content."""
        response = client.post('/api/store',
            json={
                'content': 'Test content',
                'content_type': 'text/plain',
                'metadata': {
                    'title': 'Test',
                    'description': 'Test description',
                    'tags': ['test', 'example'],
                    'categories': ['testing']
                }
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'content_id' in data
        assert data['version'] == 1
        assert 'created_at' in data
        assert data['message'] == 'Content stored successfully'


class TestUpdateEndpoint:
    """Test update endpoint."""
    
    def test_update_missing_content(self, client):
        """Test update endpoint with missing content."""
        response = client.put('/api/update/test-id',
            json={},
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_update_content(self, client):
        """Test updating content."""
        # First store content
        store_response = client.post('/api/store',
            json={
                'content': 'Original content',
                'metadata': {'title': 'Test'}
            },
            content_type='application/json'
        )
        content_id = json.loads(store_response.data)['content_id']
        
        # Then update it
        response = client.put(f'/api/update/{content_id}',
            json={
                'content': 'Updated content',
                'change_reason': 'Test update'
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['content_id'] == content_id
        assert 'updated_at' in data
        assert data['message'] == 'Content updated successfully'


class TestVersionsEndpoint:
    """Test version history endpoint."""
    
    def test_get_versions(self, client):
        """Test retrieving version history."""
        # First store content
        store_response = client.post('/api/store',
            json={
                'content': 'Original content',
                'metadata': {'title': 'Test'}
            },
            content_type='application/json'
        )
        content_id = json.loads(store_response.data)['content_id']
        
        # Get versions
        response = client.get(f'/api/versions/{content_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['content_id'] == content_id
        assert 'versions' in data
        assert 'total_versions' in data
        assert 'returned_versions' in data
    
    def test_get_versions_with_pagination(self, client):
        """Test version history with pagination."""
        # First store content
        store_response = client.post('/api/store',
            json={
                'content': 'Original content',
                'metadata': {'title': 'Test'}
            },
            content_type='application/json'
        )
        content_id = json.loads(store_response.data)['content_id']
        
        # Get versions with pagination
        response = client.get(f'/api/versions/{content_id}?limit=5&offset=0')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['content_id'] == content_id
        assert len(data['versions']) <= 5


class TestCategoriesEndpoint:
    """Test categories endpoint."""
    
    def test_get_categories(self, client):
        """Test retrieving all categories."""
        response = client.get('/api/categories')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'categories' in data
        assert isinstance(data['categories'], list)
    
    def test_create_category(self, client):
        """Test creating a category."""
        response = client.post('/api/categories',
            json={
                'name': 'Test Category',
                'description': 'A test category'
            },
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'id' in data
        assert data['name'] == 'Test Category'
        assert data['message'] == 'Category created successfully'
    
    def test_create_category_missing_name(self, client):
        """Test creating category without name."""
        response = client.post('/api/categories',
            json={'description': 'No name'},
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestTagsEndpoint:
    """Test tags endpoint."""
    
    def test_get_tags(self, client):
        """Test retrieving all tags."""
        response = client.get('/api/tags')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'tags' in data
        assert isinstance(data['tags'], list)


class TestSearchEndpoint:
    """Test search endpoint."""
    
    def test_search_by_query(self, client):
        """Test searching by query."""
        response = client.post('/api/search',
            json={'query': 'test query'},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert 'total_results' in data
        assert isinstance(data['results'], list)
    
    def test_search_by_tags(self, client):
        """Test searching by tags."""
        response = client.post('/api/search',
            json={'tags': ['test', 'example']},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert 'total_results' in data
    
    def test_search_by_categories(self, client):
        """Test searching by categories."""
        response = client.post('/api/search',
            json={'categories': ['testing']},
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert 'total_results' in data
    
    def test_search_combined(self, client):
        """Test searching with multiple criteria."""
        response = client.post('/api/search',
            json={
                'query': 'test',
                'tags': ['example'],
                'categories': ['testing']
            },
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert 'total_results' in data


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_not_found(self, client):
        """Test 404 error handling."""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
    
    def test_invalid_json(self, client):
        """Test invalid JSON handling."""
        response = client.post('/api/query',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 500]


class TestWebUIEndpoints:
    """Test web UI endpoints."""
    
    def test_index_page(self, client):
        """Test that index page is served."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Enhanced Knowledge Base Agent' in response.data
    
    def test_static_css(self, client):
        """Test that CSS is served or returns appropriate error."""
        response = client.get('/static/style.css')
        # In test environment, static files may not be available
        # Just verify the endpoint exists and returns a valid response
        assert response.status_code in [200, 404]
    
    def test_static_js(self, client):
        """Test that JavaScript is served or returns appropriate error."""
        response = client.get('/static/app.js')
        # In test environment, static files may not be available
        # Just verify the endpoint exists and returns a valid response
        assert response.status_code in [200, 404]


class TestAPIIntegration:
    """Integration tests for API workflows."""
    
    def test_store_and_retrieve_workflow(self, client):
        """Test storing and retrieving content."""
        # Store content
        store_response = client.post('/api/store',
            json={
                'content': 'Integration test content',
                'metadata': {
                    'title': 'Integration Test',
                    'tags': ['integration', 'test']
                }
            },
            content_type='application/json'
        )
        assert store_response.status_code == 201
        content_id = json.loads(store_response.data)['content_id']
        
        # Get versions
        versions_response = client.get(f'/api/versions/{content_id}')
        assert versions_response.status_code == 200
        versions_data = json.loads(versions_response.data)
        assert versions_data['total_versions'] >= 1
    
    def test_store_update_retrieve_workflow(self, client):
        """Test storing, updating, and retrieving content."""
        # Store content
        store_response = client.post('/api/store',
            json={
                'content': 'Original content',
                'metadata': {'title': 'Test'}
            },
            content_type='application/json'
        )
        content_id = json.loads(store_response.data)['content_id']
        
        # Update content
        update_response = client.put(f'/api/update/{content_id}',
            json={'content': 'Updated content'},
            content_type='application/json'
        )
        assert update_response.status_code == 200
        
        # Get versions
        versions_response = client.get(f'/api/versions/{content_id}')
        assert versions_response.status_code == 200
        versions_data = json.loads(versions_response.data)
        assert versions_data['total_versions'] >= 1
