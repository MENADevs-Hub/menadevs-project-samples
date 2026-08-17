"""Structured logging configuration for the pipeline."""

from __future__ import annotations

import logging

LOGGER_NAME = "pipeline"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Return the pipeline logger, configuring a single stream handler once."""
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
