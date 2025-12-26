# Enhanced Knowledge Base Agent

A sophisticated knowledge management system built on top of Strands agents that provides enterprise-grade information management capabilities.

## Project Structure

```
enhanced_kb_agent/
├── __init__.py                 # Package initialization
├── agent.py                    # Main agent orchestrator
├── config.py                   # Configuration management
├── exceptions.py               # Custom exceptions
├── types.py                    # Type definitions
├── core/                       # Core components
│   ├── __init__.py
│   ├── query_decomposer.py     # Query decomposition logic
│   ├── retrieval_planner.py    # Retrieval planning
│   ├── multi_step_reasoner.py  # Multi-step reasoning
│   ├── result_synthesizer.py   # Result synthesis
│   ├── information_manager.py  # Information storage/versioning
│   ├── content_processor.py    # Multi-modal content processing
│   └── knowledge_organizer.py  # Categorization and tagging
└── testing/                    # Testing utilities
    ├── __init__.py
    └── generators.py           # Hypothesis generators for PBT
```

## Core Components

### QueryDecomposer
Analyzes complex queries and breaks them into simpler sub-queries for multi-step retrieval.

### RetrievalPlanner
Creates optimized execution plans for multi-step queries, handling dependencies and ordering.

### MultiStepReasoner
Executes complex reasoning chains across multiple retrieval steps while maintaining context.

### ResultSynthesizer
Combines results from multiple retrieval steps into coherent answers with conflict detection.

### InformationManager
Handles storage, updating, and versioning of information with full audit trails.

### ContentProcessor
Processes and stores different content types (text, images, documents) with metadata extraction.

### KnowledgeOrganizer
Manages categorization and tagging of information for intelligent organization.

## Configuration

Configuration is managed through the `KnowledgeBaseConfig` class which supports:

- Environment variable overrides
- File-based configuration (JSON)
- Programmatic configuration

### Example Configuration

```python
from enhanced_kb_agent.config import KnowledgeBaseConfig

config = KnowledgeBaseConfig(
    kb_id="my-kb",
    kb_name="My Knowledge Base",
    min_score=0.5,
    max_results=10,
    cache_enabled=True,
    enable_versioning=True,
)
```

## Testing

The project uses Hypothesis for property-based testing and pytest for unit tests.

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_config.py -v

# Run with coverage
pytest tests/ --cov=enhanced_kb_agent
```

### Property-Based Testing

Hypothesis generators are provided in `enhanced_kb_agent/testing/generators.py` for generating test data:

- `query_generator`: Generate query strings
- `entity_generator`: Generate Entity instances
- `relationship_generator`: Generate Relationship instances
- `content_generator`: Generate Content instances
- `metadata_generator`: Generate Metadata instances

## Usage

### Basic Usage

```python
from enhanced_kb_agent.agent import EnhancedKnowledgeBaseAgent
from enhanced_kb_agent.config import KnowledgeBaseConfig

# Create agent with default config
agent = EnhancedKnowledgeBaseAgent()

# Or with custom config
config = KnowledgeBaseConfig(kb_id="my-kb")
agent = EnhancedKnowledgeBaseAgent(config)

# Query the knowledge base
answer = agent.query("What is the capital of France?")

# Store information
agent.store(content, metadata)

# Update information
agent.update(content_id, new_content)
```

## Requirements

- Python 3.8+
- boto3
- pytest
- hypothesis

See `enhanced_kb_agent_requirements.txt` for full dependencies.
