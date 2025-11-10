"""
Unit tests for Lecture Insight Agent workflow
"""
import pytest
import asyncio
import os
from agents.lecture_insight.workflow import execute_workflow, get_workflow

# Enable mock mode for all tests
os.environ["USE_MOCK"] = "true"


class TestWorkflowArchitecture:
    """Test workflow singleton pattern and caching."""
    
    def test_workflow_singleton(self):
        """Workflow should be compiled once and reused."""
        workflow1 = get_workflow()
        workflow2 = get_workflow()
        assert workflow1 is workflow2, "Workflow should be singleton"
    
    @pytest.mark.asyncio
    async def test_normal_execution(self):
        """Test normal workflow execution."""
        result = await execute_workflow({
            'audio_input': {'type': 'url', 'data': 'https://example.com/ml.mp3', 'format': 'mp3'},
            'session_id': 'test-1',
            'user_id': 'user-1',
            'preferences': {'resource_limit': 5}
        })
        
        assert result['transcript'], "Should have transcript"
        assert result['summary'], "Should have summary"
        assert len(result['keywords']) > 0, "Should have keywords"
        assert len(result['articles']) + len(result['videos']) == 5, "Should respect resource limit"
        assert not result['error'], "Should not have errors"
    
    @pytest.mark.asyncio
    async def test_different_topics(self):
        """Test that different audio URLs produce different content."""
        result1 = await execute_workflow({
            'audio_input': {'type': 'url', 'data': 'https://example.com/ml.mp3', 'format': 'mp3'},
            'session_id': 'test-2a',
            'user_id': 'user-1',
            'preferences': {'resource_limit': 5}
        })
        
        result2 = await execute_workflow({
            'audio_input': {'type': 'url', 'data': 'https://example.com/python.mp3', 'format': 'mp3'},
            'session_id': 'test-2b',
            'user_id': 'user-1',
            'preferences': {'resource_limit': 5}
        })
        
        assert result1['keywords'] != result2['keywords'], "Different topics should have different keywords"


class TestInputValidation:
    """Test input validation and error handling."""
    
    @pytest.mark.asyncio
    async def test_missing_audio_input(self):
        """Workflow should fail gracefully with missing audio_input."""
        result = await execute_workflow({
            'session_id': 'test-3',
            'user_id': 'user-1'
        })
        
        assert result['error'], "Should have error"
        assert "audio_input" in result['error'].lower(), "Error should mention missing field"
    
    @pytest.mark.asyncio
    async def test_missing_session_id(self):
        """Workflow should fail gracefully with missing session_id."""
        result = await execute_workflow({
            'audio_input': {'type': 'url', 'data': 'https://example.com/test.mp3', 'format': 'mp3'},
            'user_id': 'user-1'
        })
        
        assert result['error'], "Should have error"
        assert "session_id" in result['error'].lower(), "Error should mention missing field"


class TestResourceLimits:
    """Test resource limit enforcement."""
    
    @pytest.mark.asyncio
    async def test_resource_limit_3(self):
        """Test resource limit of 3."""
        result = await execute_workflow({
            'audio_input': {'type': 'url', 'data': 'https://example.com/test.mp3', 'format': 'mp3'},
            'session_id': 'test-4a',
            'user_id': 'user-1',
            'preferences': {'resource_limit': 3}
        })
        
        total = len(result['articles']) + len(result['videos'])
        assert total == 3, f"Expected 3 resources, got {total}"
    
    @pytest.mark.asyncio
    async def test_resource_limit_10(self):
        """Test resource limit of 10."""
        result = await execute_workflow({
            'audio_input': {'type': 'url', 'data': 'https://example.com/test.mp3', 'format': 'mp3'},
            'session_id': 'test-4b',
            'user_id': 'user-1',
            'preferences': {'resource_limit': 10}
        })
        
        total = len(result['articles']) + len(result['videos'])
        assert total == 10, f"Expected 10 resources, got {total}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
