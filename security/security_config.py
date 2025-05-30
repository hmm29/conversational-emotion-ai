import os
import hashlib
import secrets
import logging
from typing import Dict, List, Optional
from cryptography.fernet import Fernet
import streamlit as st
import time

logger = logging.getLogger(__name__)

class SecurityManager:
    """Handle security configurations and API key management"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_file = "security/.encryption_key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Create new key
            key = Fernet.generate_key()
            os.makedirs("security", exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key for storage"""
        encrypted_key = self.cipher_suite.encrypt(api_key.encode())
        return encrypted_key.decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key for use"""
        decrypted_key = self.cipher_suite.decrypt(encrypted_key.encode())
        return decrypted_key.decode()
    
    def validate_api_key_format(self, api_key: str, key_type: str) -> bool:
        """Validate API key format"""
        if not api_key or len(api_key) < 10:
            return False
        
        # Basic format validation
        if key_type == "openai" and not api_key.startswith("sk-"):
            return False
        
        return True
    
    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def hash_user_data(self, data: str) -> str:
        """Hash sensitive user data"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def sanitize_input(self, user_input: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        # Remove potential script tags and harmful content
        dangerous_patterns = ['<script', '</script>', 'javascript:', 'data:']
        
        sanitized = user_input
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, '')
        
        return sanitized.strip()
    
    def check_rate_limit(self, user_id: str, max_requests: int = 100, window_minutes: int = 60) -> bool:
        """Check if user has exceeded rate limit"""
        current_time = time.time()
        
        if 'rate_limits' not in st.session_state:
            st.session_state.rate_limits = {}
        
        user_requests = st.session_state.rate_limits.get(user_id, [])
        
        # Remove old requests outside the window
        window_start = current_time - (window_minutes * 60)
        user_requests = [req_time for req_time in user_requests if req_time > window_start]
        
        if len(user_requests) >= max_requests:
            return False
        
        # Add current request
        user_requests.append(current_time)
        st.session_state.rate_limits[user_id] = user_requests
        
        return True

class ConfigValidator:
    """Validate configuration and environment settings"""
    
    @staticmethod
    def validate_environment() -> Dict[str, bool]:
        """Validate that all required environment variables are set"""
        required_vars = [
            'OPENAI_API_KEY',
            'HUME_API_KEY',
            'HUME_SECRET_KEY'
        ]
        
        results = {}
        for var in required_vars:
            value = os.getenv(var)
            results[var] = bool(value and len(value) > 10)
        
        return results
    
    @staticmethod
    def validate_streamlit_config() -> Dict[str, bool]:
        """Validate Streamlit configuration"""
        return {
            'page_config_set': hasattr(st, '_config'),
            'session_state_available': hasattr(st, 'session_state'),
        }
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Get system information for debugging"""
        import platform
        import sys
        
        return {
            'python_version': sys.version,
            'platform': platform.platform(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor()
        }

def setup_security_headers():
    """Set up security headers for the Streamlit app"""
    st.markdown("""
    <script>
        // Basic XSS protection
        if (typeof window !== 'undefined') {
            window.addEventListener('beforeunload', function() {
                // Clear sensitive data
                sessionStorage.clear();
            });
        }
    </script>
    """, unsafe_allow_html=True)

# Initialize security manager
security_manager = SecurityManager()

# Setup security headers
setup_security_headers()
