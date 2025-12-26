"""Hypothesis generators for property-based testing."""

from hypothesis import strategies as st
from enhanced_kb_agent.types import (
    Entity, Relationship, Content, Metadata, SubQuery, QueryType, ContentType, Category, Tag
)
from datetime import datetime


# Basic string generators
query_text = st.text(min_size=1, max_size=500)
entity_name = st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1, max_size=100)
entity_type = st.sampled_from(['PERSON', 'ORGANIZATION', 'LOCATION', 'PRODUCT', 'OTHER'])
relationship_type = st.sampled_from(['related_to', 'part_of', 'contains', 'created_by', 'used_by'])
category_name = st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1, max_size=100)
tag_name = st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1, max_size=50)


@st.composite
def entity_generator(draw):
    """Generate Entity instances for testing."""
    return Entity(
        name=draw(entity_name),
        entity_type=draw(entity_type),
        confidence=draw(st.floats(min_value=0.0, max_value=1.0)),
    )


@st.composite
def relationship_generator(draw):
    """Generate Relationship instances for testing."""
    return Relationship(
        source_entity=draw(entity_name),
        target_entity=draw(entity_name),
        relationship_type=draw(relationship_type),
        confidence=draw(st.floats(min_value=0.0, max_value=1.0)),
    )


@st.composite
def content_generator(draw):
    """Generate Content instances for testing."""
    return Content(
        id=draw(st.uuids()).hex,
        content_type=draw(st.sampled_from(ContentType)),
        data=draw(st.text(min_size=1, max_size=1000)),
        created_by=draw(st.text(min_size=1, max_size=50)),
    )


@st.composite
def metadata_generator(draw):
    """Generate Metadata instances for testing."""
    return Metadata(
        content_id=draw(st.uuids()).hex,
        title=draw(st.text(min_size=1, max_size=200)),
        description=draw(st.text(min_size=0, max_size=500)),
        tags=draw(st.lists(st.text(min_size=1, max_size=50), max_size=10)),
        categories=draw(st.lists(st.text(min_size=1, max_size=50), max_size=5)),
        source=draw(st.text(min_size=1, max_size=100)),
        confidence_score=draw(st.floats(min_value=0.0, max_value=1.0)),
    )


@st.composite
def query_generator(draw):
    """Generate query strings for testing."""
    return draw(query_text)


@st.composite
def subquery_generator(draw):
    """Generate SubQuery instances for testing."""
    return SubQuery(
        id=draw(st.uuids()).hex,
        original_query=draw(query_text),
        sub_query_text=draw(query_text),
        query_type=draw(st.sampled_from(QueryType)),
        entities=draw(st.lists(entity_generator(), max_size=5)),
        priority=draw(st.integers(min_value=0, max_value=10)),
        dependencies=draw(st.lists(st.uuids().map(lambda x: x.hex), max_size=3)),
    )


@st.composite
def category_generator(draw):
    """Generate Category instances for testing."""
    return Category(
        id=draw(st.uuids()).hex,
        name=draw(category_name),
        description=draw(st.text(min_size=0, max_size=200)),
        parent_category=None,
        children_categories=[],
        content_count=draw(st.integers(min_value=0, max_value=100)),
    )


@st.composite
def tag_generator(draw):
    """Generate Tag instances for testing."""
    return Tag(
        id=draw(st.uuids()).hex,
        name=draw(tag_name),
        description=draw(st.text(min_size=0, max_size=200)),
        usage_count=draw(st.integers(min_value=0, max_value=100)),
        related_tags=[],
    )
