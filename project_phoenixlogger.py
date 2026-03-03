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