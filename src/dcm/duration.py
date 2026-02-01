"""
Go Duration parser for Pydantic models.

This module provides utilities to parse Go-style duration strings (e.g., "1h30m", "5s", "100ms")
into Python timedelta objects for use with Pydantic models.
"""

import re
from datetime import timedelta
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class GoDuration(timedelta):
    """
    A timedelta subclass that can parse Go-style duration strings.

    Go duration strings support the following units:
    - ns (nanoseconds)
    - us or µs (microseconds)
    - ms (milliseconds)
    - s (seconds)
    - m (minutes)
    - h (hours)

    Examples:
        - "300ms" -> 0.3 seconds
        - "1.5s" -> 1.5 seconds
        - "2m" -> 2 minutes
        - "1h30m" -> 1 hour 30 minutes
        - "24h" -> 24 hours
    """

    # Regex pattern to match Go duration format
    # Matches patterns like: 1h, 30m, 45s, 100ms, 1h30m45s, 1.5s, etc.
    DURATION_PATTERN = re.compile(
        r"^(?:(\d+(?:\.\d+)?)h)?(?:(\d+(?:\.\d+)?)m(?!s))?(?:(\d+(?:\.\d+)?)s)?(?:(\d+(?:\.\d+)?)ms)?(?:(\d+(?:\.\d+)?)(?:us|µs))?(?:(\d+(?:\.\d+)?)ns)?$"
    )

    @classmethod
    def parse_go_duration(cls, duration_str: str) -> timedelta:
        """
        Parse a Go duration string into a Python timedelta object.

        Args:
            duration_str: A Go-style duration string (e.g., "1h30m", "5s", "100ms")

        Returns:
            A timedelta object representing the duration

        Raises:
            ValueError: If the duration string is invalid
        """
        if not isinstance(duration_str, str):
            raise ValueError(f"Duration must be a string, got {type(duration_str)}")

        duration_str = duration_str.strip()
        if not duration_str:
            raise ValueError("Duration string cannot be empty")

        match = cls.DURATION_PATTERN.match(duration_str)
        if not match:
            raise ValueError(f"Invalid Go duration format: '{duration_str}'")

        hours, minutes, seconds, milliseconds, microseconds, nanoseconds = (
            match.groups()
        )

        total_seconds = 0.0

        if hours:
            total_seconds += float(hours) * 3600
        if minutes:
            total_seconds += float(minutes) * 60
        if seconds:
            total_seconds += float(seconds)
        if milliseconds:
            total_seconds += float(milliseconds) / 1000
        if microseconds:
            total_seconds += float(microseconds) / 1_000_000
        if nanoseconds:
            total_seconds += float(nanoseconds) / 1_000_000_000

        if total_seconds == 0:
            raise ValueError(f"Invalid Go duration format: '{duration_str}'")

        return timedelta(seconds=total_seconds)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Pydantic v2 schema for parsing Go duration strings.
        """

        def validate_from_str(value: Any) -> timedelta:
            if isinstance(value, timedelta):
                return value
            if isinstance(value, str):
                return cls.parse_go_duration(value)
            raise ValueError(
                f"Expected string or timedelta, got {type(value).__name__}"
            )

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.union_schema(
                    [
                        core_schema.is_instance_schema(timedelta),
                        core_schema.str_schema(),
                    ]
                ),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=from_str_schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: instance.total_seconds()
            ),
        )
