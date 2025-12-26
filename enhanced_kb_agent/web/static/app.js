// Enhanced Knowledge Base Agent - Frontend Application

const API_BASE = '/api';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupTabNavigation();
    loadInitialData();
    checkAPIStatus();
    setInterval(checkAPIStatus, 30000); // Check every 30 seconds
});

// Tab Navigation
function setupTabNavigation() {
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked button
    event.target.closest('.tab-button').classList.add('active');
}

// Initial Data Loading
async function loadInitialData() {
    try {
        // Load tags
        await loadTags();
        await loadTagsDisplay();
        
        // Load categories
        await loadCategories();
        await loadCategoriesDisplay();
        
        // Update stats
        updateStats();
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}

// API Status Check
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const statusIndicator = document.getElementById('api-status');
        const footerStatus = document.getElementById('footer-status');
        
        if (response.ok) {
            statusIndicator.innerHTML = '<span class="status-dot"></span><span style="color: #4caf50;">Online</span>';
            footerStatus.textContent = 'Online';
            footerStatus.className = 'status-online';
        } else {
            statusIndicator.innerHTML = '<span class="status-dot" style="background: #f44336;"></span><span style="color: #f44336;">Offline</span>';
            footerStatus.textContent = 'Offline';
            footerStatus.className = 'status-offline';
        }
    } catch (error) {
        const statusIndicator = document.getElementById('api-status');
        const footerStatus = document.getElementById('footer-status');
        statusIndicator.innerHTML = '<span class="status-dot" style="background: #f44336;"></span><span style="color: #f44336;">Offline</span>';
        footerStatus.textContent = 'Offline';
        footerStatus.className = 'status-offline';
    }
}

// Update Statistics
async function updateStats() {
    try {
        const tagsResponse = await fetch(`${API_BASE}/tags`);
        const categoriesResponse = await fetch(`${API_BASE}/categories`);
        
        if (tagsResponse.ok && categoriesResponse.ok) {
            const tagsData = await tagsResponse.json();
            const categoriesData = await categoriesResponse.json();
            
            document.getElementById('total-tags').textContent = tagsData.tags.length;
            document.getElementById('total-categories').textContent = categoriesData.categories.length;
            document.getElementById('storage-tags').textContent = tagsData.tags.length;
            document.getElementById('storage-categories').textContent = categoriesData.categories.length;
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// ============ QUERY TAB ============

async function executeQuery() {
    const queryInput = document.getElementById('query-input').value.trim();
    
    if (!queryInput) {
        showAlert('Please enter a query', 'error');
        return;
    }
    
    try {
        showLoading('query-results', true);
        
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: queryInput })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayQueryResults(data);
    } catch (error) {
        console.error('Error executing query:', error);
        showAlert('Error executing query: ' + error.message, 'error');
    } finally {
        showLoading('query-results', false);
    }
}

function displayQueryResults(data) {
    const resultsContainer = document.getElementById('query-results');
    const answerBox = document.getElementById('query-answer');
    const reasoningBox = document.getElementById('query-reasoning');
    const sourcesBox = document.getElementById('query-sources');
    
    // Display answer
    answerBox.innerHTML = `
        <h4>Answer</h4>
        <p>${escapeHtml(data.answer || 'No answer available')}</p>
        <p style="color: #999; font-size: 0.9em;">Confidence: ${((data.confidence || 0) * 100).toFixed(1)}%</p>
    `;
    
    // Display reasoning steps
    if (data.reasoning_steps && data.reasoning_steps.length > 0) {
        let reasoningHtml = '<h4>Reasoning Steps</h4>';
        data.reasoning_steps.forEach((step, index) => {
            reasoningHtml += `
                <div class="reasoning-step">
                    <strong>Step ${step.step_number}:</strong> ${escapeHtml(step.query)}<br>
                    <small>Results: ${step.results_count} | Time: ${step.execution_time_ms.toFixed(2)}ms | Status: ${step.success ? '✓ Success' : '✗ Failed'}</small>
                </div>
            `;
        });
        reasoningBox.innerHTML = reasoningHtml;
    } else {
        reasoningBox.innerHTML = '<h4>Reasoning Steps</h4><p>No reasoning steps available</p>';
    }
    
    // Display sources
    let sourcesHtml = '<h4>Sources</h4>';
    if (data.sources && data.sources.length > 0) {
        data.sources.forEach(source => {
            sourcesHtml += `<div class="source-item">✓ ${escapeHtml(source)}</div>`;
        });
    } else {
        sourcesHtml += '<p>No sources available</p>';
    }
    
    // Display conflicts if any
    if (data.conflicts_detected && data.conflicts_detected.length > 0) {
        sourcesHtml += '<h4 style="color: #ff6b6b; margin-top: 15px;">⚠ Conflicts Detected</h4>';
        data.conflicts_detected.forEach(conflict => {
            sourcesHtml += `<div class="source-item" style="background: #ffe0e0; border-left-color: #f44336;">⚠ ${escapeHtml(conflict)}</div>`;
        });
    }
    
    sourcesBox.innerHTML = sourcesHtml;
    resultsContainer.style.display = 'block';
}

// ============ STORE TAB ============

async function storeContent() {
    const content = document.getElementById('store-content').value.trim();
    const title = document.getElementById('store-title').value.trim();
    const description = document.getElementById('store-description').value.trim();
    const tags = document.getElementById('store-tags').value.split(',').map(t => t.trim()).filter(t => t);
    const categories = document.getElementById('store-categories').value.split(',').map(c => c.trim()).filter(c => c);
    
    if (!content) {
        showAlert('Please enter content to store', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/store`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: content,
                content_type: 'text/plain',
                metadata: {
                    title: title || 'Untitled',
                    description: description,
                    tags: tags,
                    categories: categories,
                    source: 'web-ui'
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Show success message
        showAlert(`✓ Content stored successfully! ID: ${data.content_id}`, 'success');
        
        // Clear form
        document.getElementById('store-content').value = '';
        document.getElementById('store-title').value = '';
        document.getElementById('store-description').value = '';
        document.getElementById('store-tags').value = '';
        document.getElementById('store-categories').value = '';
        
        // Update stats
        updateStats();
    } catch (error) {
        console.error('Error storing content:', error);
        showAlert('Error storing content: ' + error.message, 'error');
    }
}

// ============ SEARCH TAB ============

async function searchByQuery() {
    const query = document.getElementById('search-query').value.trim();
    
    if (!query) {
        showAlert('Please enter a search query', 'error');
        return;
    }
    
    try {
        showLoading('search-results', true);
        
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displaySearchResults(data.results || []);
    } catch (error) {
        console.error('Error searching:', error);
        showAlert('Error searching: ' + error.message, 'error');
    } finally {
        showLoading('search-results', false);
    }
}

function displaySearchResults(results) {
    const resultsContainer = document.getElementById('search-results');
    const itemsContainer = document.getElementById('search-items');
    
    if (results.length === 0) {
        itemsContainer.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">No results found</p>';
    } else {
        itemsContainer.innerHTML = results.map(result => `
            <div class="search-item">
                <h4>${escapeHtml(result.title || 'Untitled')}</h4>
                <p class="relevance">Relevance: ${((result.relevance || 0) * 100).toFixed(1)}%</p>
                <small>ID: ${escapeHtml(result.content_id)}</small>
            </div>
        `).join('');
    }
    
    resultsContainer.style.display = 'block';
}

// ============ TAG FUNCTIONS ============

async function loadTags() {
    try {
        const response = await fetch(`${API_BASE}/tags`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const tagsContainer = document.getElementById('tags-list');
        
        if (data.tags && data.tags.length > 0) {
            tagsContainer.innerHTML = data.tags.map(tag => `
                <div class="tag-item" onclick="toggleTag(this, '${escapeHtml(tag.name)}')">${escapeHtml(tag.name)}</div>
            `).join('');
        } else {
            tagsContainer.innerHTML = '<p style="color: #999;">No tags available</p>';
        }
    } catch (error) {
        console.error('Error loading tags:', error);
    }
}

async function loadTagsDisplay() {
    try {
        const response = await fetch(`${API_BASE}/tags`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const tagsDisplay = document.getElementById('tags-display');
        
        if (data.tags && data.tags.length > 0) {
            tagsDisplay.innerHTML = data.tags.map(tag => `
                <div class="tag-card">
                    <h4><i class="fas fa-tag"></i> ${escapeHtml(tag.name)}</h4>
                    <div class="count">Used ${tag.usage_count || 0} times</div>
                </div>
            `).join('');
        } else {
            tagsDisplay.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">No tags available</p>';
        }
    } catch (error) {
        console.error('Error loading tags:', error);
    }
}

function toggleTag(element, tagName) {
    element.classList.toggle('selected');
}

// ============ CATEGORY FUNCTIONS ============

async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const categoriesContainer = document.getElementById('categories-list');
        
        if (data.categories && data.categories.length > 0) {
            categoriesContainer.innerHTML = data.categories.map(cat => `
                <div class="category-item" onclick="toggleCategory(this, '${escapeHtml(cat.id)}')">${escapeHtml(cat.name)}</div>
            `).join('');
        } else {
            categoriesContainer.innerHTML = '<p style="color: #999;">No categories available</p>';
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadCategoriesDisplay() {
    try {
        const response = await fetch(`${API_BASE}/categories`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const categoriesDisplay = document.getElementById('categories-display');
        
        if (data.categories && data.categories.length > 0) {
            categoriesDisplay.innerHTML = data.categories.map(cat => `
                <div class="category-card">
                    <h4><i class="fas fa-folder"></i> ${escapeHtml(cat.name)}</h4>
                    <p>${escapeHtml(cat.description || 'No description')}</p>
                    <div class="count">${cat.content_count || 0} items</div>
                </div>
            `).join('');
        } else {
            categoriesDisplay.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">No categories available</p>';
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function toggleCategory(element, categoryId) {
    element.classList.toggle('selected');
}

async function createCategory() {
    const name = document.getElementById('category-name').value.trim();
    const description = document.getElementById('category-description').value.trim();
    
    if (!name) {
        showAlert('Please enter a category name', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/categories`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        showAlert(`✓ Category "${data.name}" created successfully!`, 'success');
        
        // Clear form
        document.getElementById('category-name').value = '';
        document.getElementById('category-description').value = '';
        
        // Refresh categories display
        await loadCategoriesDisplay();
        await loadCategories();
        updateStats();
    } catch (error) {
        console.error('Error creating category:', error);
        showAlert('Error creating category: ' + error.message, 'error');
    }
}

// ============ UTILITY FUNCTIONS ============

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `result-message ${type}`;
    alert.innerHTML = message;
    alert.style.position = 'fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.style.maxWidth = '400px';
    alert.style.animation = 'slideIn 0.3s ease';
    
    document.body.appendChild(alert);
    
    // Remove after 5 seconds
    setTimeout(() => {
        alert.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

function showLoading(elementId, show) {
    const element = document.getElementById(elementId);
    if (element) {
        if (show) {
            element.innerHTML = '<div style="text-align: center; padding: 20px;"><div class="loading"></div><p>Loading...</p></div>';
        }
    }
}

// Add slide animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
