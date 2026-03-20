"""Output parser for CLI agent responses.

Extracts structured JSON data from mixed CLI output that may contain
non-JSON text before and after the JSON payload.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class OutputParser:
    """Parses and extracts JSON from CLI tool output.

    CLI tools often emit non-JSON text (progress bars, logs) alongside
    their structured output.  This parser tries direct JSON parsing
    first, then falls back to extracting the first JSON object or array.
    """

    def parse_json(self, raw_output: str) -> dict[str, Any]:
        """Parse JSON from raw CLI output.

        Attempts direct ``json.loads`` first.  On failure, searches for
        the first ``{`` / ``}`` pair or ``[`` / ``]`` pair and extracts
        the substring for parsing.

        Args:
            raw_output: Raw string output from the CLI process.

        Returns:
            Parsed dict, or empty dict if no valid JSON found.
        """
        if not raw_output.strip():
            return {}

        # Try direct parse first
        try:
            result = json.loads(raw_output)
            if isinstance(result, dict):
                return result
            return {"data": result}
        except (json.JSONDecodeError, ValueError):
            pass

        # Try to find embedded JSON object
        obj_start = raw_output.find("{")
        obj_end = raw_output.rfind("}")
        if obj_start != -1 and obj_end > obj_start:
            try:
                return json.loads(raw_output[obj_start : obj_end + 1])
            except (json.JSONDecodeError, ValueError):
                pass

        # Try to find embedded JSON array
        arr_start = raw_output.find("[")
        arr_end = raw_output.rfind("]")
        if arr_start != -1 and arr_end > arr_start:
            try:
                result = json.loads(raw_output[arr_start : arr_end + 1])
                return {"data": result}
            except (json.JSONDecodeError, ValueError):
                pass

        logger.debug("No JSON found in CLI output")
        return {}

    def extract_files_modified(self, parsed: dict[str, Any]) -> list[str]:
        """Extract file paths from common CLI output structures.

        Looks for common keys used by CLI tools to report modified files
        (``files``, ``files_modified``, ``modified_files``, ``changes``).

        Args:
            parsed: Previously parsed JSON dict from CLI output.

        Returns:
            List of file path strings found in the output.
        """
        file_keys = ["files", "files_modified", "modified_files", "changes"]
        for key in file_keys:
            value = parsed.get(key)
            if isinstance(value, list):
                return [str(f) for f in value if isinstance(f, str)]
        return []
