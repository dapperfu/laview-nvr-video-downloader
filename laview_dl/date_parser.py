"""
Simple date and time parsing using the dateparser library.

This module provides robust parsing of various date/time formats using
the dateparser library, which handles natural language parsing much
better than custom regex patterns.
"""

from datetime import datetime

from dateparser import parse as dateparser_parse


class FlexibleDateParser:
    """A simple wrapper around dateparser for consistent interface."""

    @classmethod
    def parse_datetime(cls, text: str) -> datetime:
        """
        Parse a datetime string using dateparser.
        
        Args:
            text: The datetime string to parse
            
        Returns:
            Parsed datetime object
            
        Raises:
            ValueError: If the text cannot be parsed
        """
        text = text.strip()

        # Use dateparser to parse the text
        result = dateparser_parse(text)

        if result is None:
            raise ValueError(f'Unable to parse datetime: "{text}"')

        return result

    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """Get a list of supported date/time formats."""
        return [
            "Natural language: today, yesterday, tomorrow, now",
            "Relative: 2 days ago, next week, last month",
            "Formatted: August 30, 2025, 08/30/2025, 30/08/2025",
            "Combined: '8 AM yesterday', 'August 30, 2025 08:00 AM'",
            "Time formats: 4:00PM, 4:00 PM, 16:00, 4:00:00 PM",
            "And many more supported by dateparser library",
        ]
