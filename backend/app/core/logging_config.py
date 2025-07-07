import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

def setup_logging() -> Dict[str, Any]:
    """
    Set up comprehensive logging configuration for the OVRA AI backend.
    Creates daily rotating log files in the logs directory.
    """
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Get current date for log file naming
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Define log file paths
    app_log_file = logs_dir / f"app_{current_date}.log"
    api_log_file = logs_dir / f"api_{current_date}.log"
    chat_log_file = logs_dir / f"chat_{current_date}.log"
    auth_log_file = logs_dir / f"auth_{current_date}.log"
    error_log_file = logs_dir / f"errors_{current_date}.log"
    
    # Define log format
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    # Main application log handler (daily rotation)
    app_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(app_log_file),
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding="utf-8"
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(log_format)
    
    # Error log handler (errors and above only)
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(error_log_file),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers for different modules
    configure_module_loggers(logs_dir, current_date, log_format)
    
    # Configure third-party loggers
    configure_third_party_loggers()
    
    logging.info("Logging system initialized successfully")
    logging.info(f"Log files will be stored in: {logs_dir.absolute()}")
    
    return {
        "logs_dir": str(logs_dir.absolute()),
        "log_files": {
            "app": str(app_log_file),
            "api": str(api_log_file),
            "chat": str(chat_log_file),
            "auth": str(auth_log_file),
            "errors": str(error_log_file)
        }
    }

def configure_module_loggers(logs_dir: Path, current_date: str, log_format: logging.Formatter):
    """Configure specific loggers for different application modules."""
    
    # API requests logger
    api_logger = logging.getLogger("ovra.api")
    api_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(logs_dir / f"api_{current_date}.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    api_handler.setFormatter(log_format)
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    
    # Chat service logger
    chat_logger = logging.getLogger("ovra.chat")
    chat_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(logs_dir / f"chat_{current_date}.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    chat_handler.setFormatter(log_format)
    chat_logger.addHandler(chat_handler)
    chat_logger.setLevel(logging.INFO)
    
    # Authentication logger
    auth_logger = logging.getLogger("ovra.auth")
    auth_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(logs_dir / f"auth_{current_date}.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    auth_handler.setFormatter(log_format)
    auth_logger.addHandler(auth_handler)
    auth_logger.setLevel(logging.INFO)
    
    # Database logger
    db_logger = logging.getLogger("ovra.database")
    db_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(logs_dir / f"database_{current_date}.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    db_handler.setFormatter(log_format)
    db_logger.addHandler(db_handler)
    db_logger.setLevel(logging.INFO)

def configure_third_party_loggers():
    """Configure logging levels for third-party libraries."""
    
    # Reduce verbosity of third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"ovra.{name}")

# Convenience functions for common logging scenarios
def log_api_request(endpoint: str, method: str, user_id: str = None, ip_address: str = None, **kwargs):
    """Log API request details."""
    logger = get_logger("api")
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    log_msg = f"API Request: {method} {endpoint}"
    if user_id:
        log_msg += f" | User: {user_id}"
    if ip_address:
        log_msg += f" | IP: {ip_address}"
    if extra_info:
        log_msg += f" | {extra_info}"
    logger.info(log_msg)

def log_api_response(endpoint: str, method: str, status_code: int, response_time_ms: float, user_id: str = None, **kwargs):
    """Log API response details."""
    logger = get_logger("api")
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    log_msg = f"API Response: {method} {endpoint} | Status: {status_code} | Time: {response_time_ms:.2f}ms"
    if user_id:
        log_msg += f" | User: {user_id}"
    if extra_info:
        log_msg += f" | {extra_info}"
    logger.info(log_msg)

def log_chat_interaction(user_id: str, session_id: str, action: str, **kwargs):
    """Log chat interaction details."""
    logger = get_logger("chat")
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    log_msg = f"Chat {action}: User {user_id} | Session: {session_id}"
    if extra_info:
        log_msg += f" | {extra_info}"
    logger.info(log_msg)

def log_auth_event(event: str, user_id: str = None, email: str = None, success: bool = True, **kwargs):
    """Log authentication events."""
    logger = get_logger("auth")
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    status = "SUCCESS" if success else "FAILED"
    log_msg = f"Auth {event}: {status}"
    if user_id:
        log_msg += f" | User ID: {user_id}"
    if email:
        log_msg += f" | Email: {email}"
    if extra_info:
        log_msg += f" | {extra_info}"
    
    if success:
        logger.info(log_msg)
    else:
        logger.warning(log_msg)

def log_database_operation(operation: str, table: str, **kwargs):
    """Log database operations."""
    logger = get_logger("database")
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    log_msg = f"DB {operation}: {table}"
    if extra_info:
        log_msg += f" | {extra_info}"
    logger.info(log_msg)

def log_error(error: Exception, context: str = "", **kwargs):
    """Log error with context."""
    logger = logging.getLogger()
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    log_msg = f"ERROR in {context}: {str(error)}"
    if extra_info:
        log_msg += f" | {extra_info}"
    logger.error(log_msg, exc_info=True)