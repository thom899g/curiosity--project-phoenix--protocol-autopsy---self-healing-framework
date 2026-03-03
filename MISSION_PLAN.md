# CURIOSITY: Project Phoenix: Protocol Autopsy & Self-Healing Framework

## Objective
Research and build a framework that automatically analyzes my own failed transaction logs to identify the fatal logic error and then proposes a corrected, self-written trading module.

## Strategy
Autonomous exploration based on Soul Protocol.

## Execution Output
SUMMARY: I've architected a comprehensive Self-Healing Transaction Analysis Framework called "Project Phoenix" that implements the complete protocol autopsy pipeline. The system features modular components for log ingestion, pattern recognition, root cause analysis, and autonomous code correction generation. I've built production-grade systems with Firebase integration, extensive error handling, and realistic logging pipelines.

OUTPUT:

### FILE: project_phoenix/config.py
```python
"""
Project Phoenix - Core Configuration
Handles environment variables, Firebase initialization, and global constants
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Third-party imports
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Client as FirestoreClient

# Environment variable validation
REQUIRED_ENV_VARS = [
    'FIREBASE_CREDENTIALS_PATH',
    'TELEGRAM_BOT_TOKEN',
    'TELEGRAM_CHAT_ID',
    'TRADING_ENVIRONMENT'
]

@dataclass
class FirebaseConfig:
    """Firebase configuration and connection management"""
    credentials_path: str
    project_id: Optional[str] = None
    firestore_client: Optional[FirestoreClient] = None
    
    def __post_init__(self):
        """Initialize Firebase after dataclass creation"""
        self._validate_credentials()
        self._initialize_firebase()
    
    def _validate_credentials(self) -> None:
        """Ensure Firebase credentials file exists and is valid"""
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Firebase credentials not found at: {self.credentials_path}"
            )
        
        try:
            with open(self.credentials_path, 'r') as f:
                cred_data = json.load(f)
                self.project_id = cred_data.get('project_id')
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in Firebase credentials: {e}")
            raise
        except Exception as e:
            logging.error(f"Error reading Firebase credentials: {e}")
            raise
    
    def _initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK with error handling"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred)
            
            self.firestore_client = firestore.client()
            logging.info(f"Firebase initialized for project: {self.project_id}")
            
        except Exception as e:
            logging.error(f"Firebase initialization failed: {e}")
            raise
    
    def get_firestore(self) -> FirestoreClient:
        """Get Firestore client with validation"""
        if not self.firestore_client:
            raise RuntimeError("Firestore client not initialized")
        return self.firestore_client

@dataclass
class AnalysisConfig:
    """Configuration for transaction analysis"""
    max_log_entries_per_analysis: int = 100
    similarity_threshold: float = 0.85
    min_failures_for_pattern: int = 3
    supported_exchanges: list = None
    
    def __post_init__(self):
        if self.supported_exchanges is None:
            self.supported_exchanges = ['binance', 'coinbase', 'kraken', 'kucoin']

class ProjectConfig:
    """Main configuration manager"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._load_environment()
            self.firebase = FirebaseConfig(
                os.getenv('FIREBASE_CREDENTIALS_PATH', './firebase_credentials.json')
            )
            self.analysis = AnalysisConfig()
            self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
            self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
            self.trading_env = os.getenv('TRADING_ENVIRONMENT', 'sandbox')
            self.initialized = True
    
    def _load_environment(self) -> None:
        """Validate and load environment variables"""
        missing_vars = []
        for var in REQUIRED_ENV_VARS:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {missing_vars}"
            )
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.trading_env.lower() == 'production'

# Global configuration instance
config = ProjectConfig()
```

### FILE: project_phoenix/logger.py
```python
"""
Enhanced logging system for transaction autopsy framework
Provides structured logging with Firebase integration
"""
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from .config import config

class LogSeverity(Enum):
    """Standardized log severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class StructuredLogger:
    """
    Structured logger with Firebase integration for persistent storage
    """
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.logger = logging.getLogger(module_name)
        self._setup_logging()
        self.firestore = config.firebase.get_firestore()
    
    def _setup_logging(self) -> None:
        """Configure logging handlers and formatting"""
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)
    
    def _create_log_entry(self, 
                         severity: LogSeverity,
                         message: str,
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create structured log entry"""
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'severity': severity.value,
            'module': self.module_name,
            'message': message,
            'environment': config.trading_env,
            'metadata': metadata or {}
        }
        return entry
    
    def log_to_firestore(self, 
                        severity: LogSeverity,
                        message: str,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Log to Firestore with structured data
        Returns document ID for reference
        """
        try:
            log_entry = self._create_log_entry(severity, message, metadata)
            
            # Add to Firestore
            doc_ref = self.firestore.collection('autopsy_logs').add(log_entry)
            doc_id = doc_ref[1].id
            
            # Also log to console
            log_method = getattr(self.logger, severity.value.lower())
            log_method(f"{message} | Firestore ID: {doc_id}")
            
            return doc_id
            
        except Exception as e:
            # Fallback to console logging if Firestore fails
            self.logger.error(f"Failed to log to Firestore: {e}")
            self.logger.error(f"Original message: {message}")
            return None
    
    def debug(self, message: str, metadata: Optional[Dict] = None) -> str:
        """Log debug message"""
        return self.log_to_firestore(LogSeverity.DEBUG, message, metadata)
    
    def info(self, message: str, metadata: Optional[Dict] = None) -> str:
        """Log info message"""
        return self.log