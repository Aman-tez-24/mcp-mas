"""
Structured Logging Utilities
Outputs JSON-formatted logs matching PDF Section 24 specification.
"""

import datetime
import json
import logging
import sys
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "run_id"):
            log_obj["run_id"] = record.run_id
        if hasattr(record, "tool"):
            log_obj["tool"] = record.tool
        if hasattr(record, "agent"):
            log_obj["agent"] = record.agent

        return json.dumps(log_obj)


def setup_logger(name: str = "multi_agent_mcp", level: str = "INFO") -> logging.Logger:
    """Configures structured stream handler."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger


logger = setup_logger()
