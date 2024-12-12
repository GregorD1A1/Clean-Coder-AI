"""Integration tests for running single coder pipeline with no documentation context added."""

import logging
import pytest

logger = logging.getLogger()
logger.level = logging.INFO


@pytest.mark.integration
def test_llm_no_context() -> None:
    """Test that the LLM hallucinates and produces incorrect import statement without context."""
    # Given request for the LLM
    # and given the single task pipeline
    # When making the LLM call
    # Then assert that the response is as expected
    result1 = 1
    result2 = 2
    assert result1 == result2


@pytest.mark.integration
def test_llm_limited_context() -> None:
    """Test that a limited hint on documentation allows LLM to make a correct import but hallucinates on class method."""
    # Given request for the LLM
    # and given the single task pipeline
    # When making the LLM call
    # Then assert that the response is as expected
    assert 1 == 1


@pytest.mark.integration
def test_llm_raglike_context() -> None:
    """Test that a full hint on documentation allows LLM to make a correct implementation of what is requested."""
    # Given initial request for the LLM
    # and given the single task pipeline
    # When making the LLM call
    # Then assert that the response is as expected
    assert 1 == 1


def test_llm_rag_context() -> None:
    """Test that an LLM with RAG documentation makes a correct implementation of what is requested."""
    # Given initial request for the LLM
    # and given the single task pipeline
    # When making the LLM call
    # Then assert that the response is as expected
    assert 1 == 1
