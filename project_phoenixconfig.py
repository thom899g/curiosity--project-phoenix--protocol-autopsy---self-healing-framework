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