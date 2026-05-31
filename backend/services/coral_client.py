import json
import asyncio
import logging
import shutil
from typing import List, Dict, Any

from backend.services.coral_fake_data import get_fake_coral_results

logger = logging.getLogger(__name__)

# Check once at import time whether coral CLI exists
_CORAL_AVAILABLE = shutil.which("coral") is not None

if not _CORAL_AVAILABLE:
    logger.warning("Coral CLI not found — using fake demo data for all queries")


async def query_coral(sql: str) -> List[Dict[str, Any]]:
    """
    Executes a SQL query against Coral CLI and returns the parsed JSON results.
    Falls back to fake demo data when Coral CLI is not installed (hackathon mode).
    """
    # [HACKATHON MOCK] We force fake data here immediately.
    # The real Coral CLI is installed but schemas aren't registered,
    # causing 5-10 second timeouts per query which breaks the UI.
    logger.info(f"[DEMO] Coral query (fake): {sql[:80]}...")
    return get_fake_coral_results(sql)
