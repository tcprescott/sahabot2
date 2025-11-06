"""
Custom logging handler for capturing application logs in memory.

This module provides a thread-safe logging handler that stores recent log
records in a circular buffer for display in the admin UI.
"""

import logging
from collections import deque
from typing import List, Optional
from threading import Lock
from datetime import datetime, timezone


class LogRecord:
    """Structured log record for UI display."""

    def __init__(
        self,
        timestamp: datetime,
        level: str,
        logger_name: str,
        message: str,
        exc_info: Optional[str] = None
    ):
        """
        Initialize a log record.

        Args:
            timestamp: When the log was created
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            logger_name: Name of the logger that created the record
            message: Log message
            exc_info: Exception information if available
        """
        self.timestamp = timestamp
        self.level = level
        self.logger_name = logger_name
        self.message = message
        self.exc_info = exc_info

    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'logger_name': self.logger_name,
            'message': self.message,
            'exc_info': self.exc_info,
        }


class InMemoryLogHandler(logging.Handler):
    """
    Logging handler that stores recent log records in memory.

    This handler maintains a circular buffer of log records that can be
    accessed by the admin UI for real-time log viewing.
    """

    def __init__(self, max_records: int = 1000):
        """
        Initialize the log handler.

        Args:
            max_records: Maximum number of log records to keep in memory
        """
        super().__init__()
        self.max_records = max_records
        self.records: deque[LogRecord] = deque(maxlen=max_records)
        self.lock = Lock()

    def emit(self, record: logging.LogRecord):
        """
        Emit a log record.

        Args:
            record: The log record to emit
        """
        try:
            # Format the message
            message = self.format(record)

            # Get exception info if available
            exc_info = None
            if record.exc_info:
                exc_info = self.formatter.formatException(record.exc_info) if self.formatter else str(record.exc_info)

            # Create structured log record
            log_record = LogRecord(
                timestamp=datetime.fromtimestamp(record.created, tz=timezone.utc),
                level=record.levelname,
                logger_name=record.name,
                message=message,
                exc_info=exc_info
            )

            # Add to buffer (thread-safe)
            with self.lock:
                self.records.append(log_record)

        except Exception:
            self.handleError(record)

    def get_records(
        self,
        level: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[LogRecord]:
        """
        Get log records with optional filtering.

        Args:
            level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            search: Search term to filter messages
            limit: Maximum number of records to return

        Returns:
            List of log records matching the criteria
        """
        with self.lock:
            records = list(self.records)

        # Filter by level
        if level:
            records = [r for r in records if r.level == level]

        # Filter by search term
        if search:
            search_lower = search.lower()
            records = [
                r for r in records
                if search_lower in r.message.lower() or search_lower in r.logger_name.lower()
            ]

        # Limit results
        if limit:
            records = records[-limit:]

        return records

    def clear(self):
        """Clear all stored log records."""
        with self.lock:
            self.records.clear()

    def get_count(self) -> int:
        """Get the current number of stored log records."""
        with self.lock:
            return len(self.records)


# Global instance for the application
_log_handler: Optional[InMemoryLogHandler] = None


def get_log_handler() -> InMemoryLogHandler:
    """
    Get the global log handler instance.

    Returns:
        The global InMemoryLogHandler instance

    Raises:
        RuntimeError: If the log handler has not been initialized
    """
    if _log_handler is None:
        raise RuntimeError("Log handler not initialized. Call init_log_handler() first.")
    return _log_handler


def init_log_handler(max_records: int = 1000) -> InMemoryLogHandler:
    """
    Initialize the global log handler and attach it to the root logger.

    Args:
        max_records: Maximum number of log records to keep in memory

    Returns:
        The initialized InMemoryLogHandler instance
    """
    global _log_handler

    if _log_handler is not None:
        return _log_handler

    # Create handler
    _log_handler = InMemoryLogHandler(max_records=max_records)

    # Set formatter to match main.py format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    _log_handler.setFormatter(formatter)

    # Set level to capture all logs
    _log_handler.setLevel(logging.DEBUG)

    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(_log_handler)

    return _log_handler
