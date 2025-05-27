"""
Tests for utility functions.
"""
import os
import pytest
from pathlib import Path
import tempfile
import json
import yaml

# Add the src directory to the Python path
import sys
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from utils import (
    load_config,
    ensure_directory_exists,
    get_emotion_analysis_summary,
    validate_environment_variables,
    format_timestamp,
    load_json_file,
    save_json_file
)

def test_load_config_valid_yaml():
    """Test loading a valid YAML configuration file."""
    # Create a temporary YAML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({"test_key": "test_value"}, f)
    
    try:
        config = load_config(f.name)
        assert config["test_key"] == "test_value"
    finally:
        os.unlink(f.name)

def test_load_config_invalid_yaml():
    """Test loading an invalid YAML file raises an exception."""
    # Create a temporary invalid YAML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: file")
    
    try:
        with pytest.raises(yaml.YAMLError):
            load_config(f.name)
    finally:
        os.unlink(f.name)

def test_load_config_nonexistent():
    """Test loading a non-existent config file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_file.yaml")

def test_ensure_directory_exists():
    """Test that ensure_directory_exists creates directories as needed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test" / "subdir"
        
        # Directory shouldn't exist yet
        assert not test_dir.exists()
        
        # Create the directory
        result = ensure_directory_exists(test_dir)
        
        # Verify it was created
        assert test_dir.exists()
        assert test_dir.is_dir()
        assert result == test_dir

def test_get_emotion_analysis_summary():
    """Test generating a summary of emotion analysis results."""
    emotions = {
        "joy": 0.8,
        "sadness": 0.6,
        "anger": 0.3,
        "fear": 0.2,
        "surprise": 0.1,
        "disgust": 0.0
    }
    
    # Test with default top_n (3)
    summary = get_emotion_analysis_summary(emotions)
    assert "Joy: 80.0%" in summary
    assert "Sadness: 60.0%" in summary
    assert "Anger: 30.0%" in summary
    assert "Fear: 20.0%" not in summary  # Should only show top 3
    
    # Test with custom top_n
    summary = get_emotion_analysis_summary(emotions, top_n=2)
    assert "Joy: 80.0%" in summary
    assert "Sadness: 60.0%" in summary
    assert "Anger: 30.0%" not in summary  # Should only show top 2

def test_get_emotion_analysis_summary_empty():
    """Test with empty or None input."""
    assert get_emotion_analysis_summary({}) == "No emotion data available."
    assert get_emotion_analysis_summary(None) == "No emotion data available."

def test_validate_environment_variables():
    """Test validation of required environment variables."""
    # Save original environment
    original_env = {}
    for var in ['OPENAI_API_KEY', 'HUME_API_KEY', 'HUME_SECRET_KEY']:
        original_env[var] = os.environ.get(var)
    
    try:
        # Test with all variables set
        os.environ.update({
            'OPENAI_API_KEY': 'test_openai_key',
            'HUME_API_KEY': 'test_hume_key',
            'HUME_SECRET_KEY': 'test_hume_secret'
        })
        assert validate_environment_variables() is True
        
        # Test with missing variables
        os.environ.pop('OPENAI_API_KEY')
        assert validate_environment_variables() is False
        
    finally:
        # Restore original environment
        for var, value in original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

def test_format_timestamp():
    """Test timestamp formatting."""
    # Test with ISO format string
    iso_timestamp = "2023-10-27T12:34:56+00:00"
    formatted = format_timestamp(iso_timestamp)
    assert "2023-10-27 12:34:56" in formatted
    
    # Test with None (should use current time)
    current_time = format_timestamp()
    assert len(current_time) > 0
    
    # Test with invalid format
    assert format_timestamp("invalid-timestamp") == "invalid-timestamp"

def test_json_file_operations():
    """Test saving and loading JSON files."""
    test_data = {"key": "value", "nested": {"number": 42}}
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # Test saving and loading
        save_json_file(test_data, temp_path)
        loaded_data = load_json_file(temp_path)
        
        assert loaded_data == test_data
        
        # Test loading non-existent file
        with pytest.raises(FileNotFoundError):
            load_json_file("nonexistent_file.json")
            
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
