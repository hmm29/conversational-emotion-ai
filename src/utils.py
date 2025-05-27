"""
Utility functions for the Conversational Emotion AI application.
"""
import json
import logging
import os
import time
from datetime import datetime, timezone
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

import yaml
from dotenv import load_dotenv

# Type variable for generic type hinting
T = TypeVar('T')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
REQUIRED_ENV_VARS = [
    'OPENAI_API_KEY',
    'HUME_API_KEY',
    'HUME_SECRET_KEY'
]

DEFAULT_INDENT = 2
MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5

@lru_cache(maxsize=128)
def parse_iso_timestamp(timestamp: str) -> datetime:
    """Parse ISO format timestamp with timezone support.
    
    Args:
        timestamp: ISO format timestamp string.
        
    Returns:
        datetime object representing the timestamp.
        
    Raises:
        ValueError: If the timestamp format is invalid.
    """
    try:
        if timestamp.endswith('Z'):
            return datetime.fromisoformat(timestamp[:-1] + '+00:00').replace(tzinfo=timezone.utc)
        dt = datetime.fromisoformat(timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid timestamp format: {timestamp}") from e

def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file.
        
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        FileNotFoundError: If config_path doesn't exist.
        yaml.YAMLError: If the YAML is malformed.
        OSError: For other I/O related errors.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return cast(Dict[str, Any], yaml.safe_load(f) or {})
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}") from e
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration in {config_path}: {e}")
        raise yaml.YAMLError(f"Invalid YAML in {config_path}: {e}") from e
    except OSError as e:
        logger.error(f"Error reading configuration file {config_path}: {e}")
        raise OSError(f"Failed to read configuration file {config_path}") from e

def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Validate that required keys exist in config.
    """
    missing = [key for key in required_keys if key not in config]
    if missing:
        logger.error(f"Missing required config keys: {', '.join(missing)}")
        return False
    return True

def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory.
        
    Returns:
        Path object for the directory.
        
    Raises:
        OSError: If directory creation fails due to permission issues.
    """
    path = Path(directory)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        raise OSError(f"Failed to create directory {directory}") from e


def get_emotion_analysis_summary(emotions: Dict[str, float], top_n: int = 3) -> str:
    """Generate a human-readable summary of emotion analysis results.
    
    Args:
        emotions: Dictionary mapping emotion names to scores.
        top_n: Number of top emotions to include in the summary.
        
    Returns:
        Formatted string summarizing the emotions.
        
    Raises:
        ValueError: If top_n is not a positive integer.
    """
    if top_n <= 0:
        raise ValueError("top_n must be a positive integer")
        
    if not emotions:
        return "No emotion data available."
    
    try:
        # Sort emotions by score in descending order
        sorted_emotions = sorted(
            emotions.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get top N emotions
        top_emotions = sorted_emotions[:top_n]
        
        # Format the summary
        summary_parts = []
        for i, (emotion, score) in enumerate(top_emotions, 1):
            percentage = score * 100
            summary_parts.append(f"{i}. {emotion.capitalize()}: {percentage:.1f}%")
        
        return "\n".join(summary_parts)
    except (TypeError, AttributeError) as e:
        logger.error(f"Error processing emotions data: {e}")
        return "Error: Invalid emotion data format"


def validate_environment_variables(required_vars: Optional[List[str]] = None) -> bool:
    """Check if all required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names. 
                     If None, uses default REQUIRED_ENV_VARS.
                     
    Returns:
        bool: True if all required variables are set, False otherwise.
    """
    if required_vars is None:
        required_vars = REQUIRED_ENV_VARS
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True


def format_timestamp(timestamp: Optional[Union[str, datetime]] = None) -> str:
    """Format a timestamp in a human-readable format.
    
    Args:
        timestamp: Either a datetime object or ISO format timestamp string. 
                 If None, uses current time.
        
    Returns:
        Formatted date and time string in 'YYYY-MM-DD HH:MM:SS TZ' format.
    """
    if timestamp is None:
        dt = datetime.now(timezone.utc)
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        try:
            dt = parse_iso_timestamp(timestamp)
        except ValueError:
            logger.warning(f"Invalid timestamp format: {timestamp}")
            return str(timestamp)
    
    # Ensure timezone awareness
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z')


def load_json_file(filepath: Union[str, Path], 
                  model: Optional[Type[T]] = None) -> Union[Dict[str, Any], T]:
    """Load data from a JSON file with optional model validation.
    
    Args:
        filepath: Path to the JSON file.
        model: Optional Pydantic model class to validate against.
        
    Returns:
        The parsed JSON data, optionally validated against the provided model.
        
    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        ValidationError: If model is provided and validation fails.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if model is not None:
            try:
                from pydantic import ValidationError
                return model(**data)
            except ImportError:
                logger.warning("Pydantic not available, skipping model validation")
            except ValidationError as e:
                logger.error(f"Validation error in {filepath}: {e}")
                raise
                
        return data
        
    except FileNotFoundError as e:
        logger.error(f"JSON file not found: {filepath}")
        raise FileNotFoundError(f"JSON file not found: {filepath}") from e
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file {filepath}: {e}")
        raise json.JSONDecodeError(
            f"Invalid JSON in {filepath}: {e.msg}", 
            e.doc, 
            e.pos
        ) from e


def save_json_file(data: Any, 
                  filepath: Union[str, Path], 
                  indent: int = DEFAULT_INDENT,
                  ensure_ascii: bool = False) -> None:
    """Save data to a JSON file.
    
    Args:
        data: Data to save (must be JSON-serializable).
        filepath: Path where the file should be saved.
        indent: Number of spaces to use for indentation.
        ensure_ascii: If True, non-ASCII characters are escaped.
        
    Raises:
        TypeError: If the data is not JSON-serializable.
        OSError: If file cannot be written.
        ValueError: If filepath is a directory.
    """
    path = Path(filepath)
    
    if path.exists() and path.is_dir():
        raise ValueError(f"Cannot write to directory: {filepath}")
    
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Use atomic write to prevent corruption
        temp_path = path.with_suffix('.tmp')
        with temp_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        
        # Atomic rename on POSIX systems
        temp_path.replace(path)
        
        logger.debug(f"Data saved to {path}")
        
    except (TypeError, OverflowError) as e:
        logger.error(f"Data serialization error: {e}")
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()  # Clean up temp file
        raise
    except OSError as e:
        logger.error(f"Error writing to file {path}: {e}")
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()  # Clean up temp file
        raise
    except Exception as e:
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()  # Clean up temp file on any other error
        raise


def with_retry(max_retries: int = MAX_RETRIES, 
              backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
              exceptions: tuple = (Exception,)) -> Callable:
    """Decorator for retrying a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts.
        backoff_factor: Factor for exponential backoff calculation.
        exceptions: Tuple of exceptions to catch and retry on.
        
    Returns:
        Decorated function with retry logic.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            last_exception = None
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    retries += 1
                    if retries > max_retries:
                        break
                        
                    # Calculate backoff time
                    wait_time = min(
                        backoff_factor * (2 ** (retries - 1)),  # Exponential backoff
                        60  # Max 60 seconds
                    )
                    
                    logger.warning(
                        f"Attempt {retries}/{max_retries} failed: {e}. "
                        f"Retrying in {wait_time:.2f} seconds..."
                    )
                    time.sleep(wait_time)
            
            # If we've exhausted all retries, raise the last exception
            logger.error(f"All {max_retries} attempts failed")
            raise last_exception  # type: ignore
            
        return wrapper
    return decorator