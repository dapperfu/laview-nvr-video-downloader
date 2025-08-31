"""
Flexible date and time parsing for laview-nvr-video-downloader.

This module provides robust parsing of various date/time formats including:
- Standard formats (YYYY-MM-DD HH:MM:SS)
- Natural language (today, yesterday, now)
- Formatted dates (August 30, 2025)
- Relative dates (2 days ago, next week)
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
import calendar


class FlexibleDateParser:
    """A flexible parser for various date and time formats."""
    
    # Common date formats
    DATE_FORMATS = [
        "%Y-%m-%d %H:%M:%S",      # 2025-08-30 08:00:00
        "%Y-%m-%d %H:%M",         # 2025-08-30 08:00
        "%Y-%m-%d",               # 2025-08-30
        "%m/%d/%Y %H:%M:%S",      # 08/30/2025 08:00:00
        "%m/%d/%Y %H:%M",         # 08/30/2025 08:00
        "%m/%d/%Y",               # 08/30/2025
        "%d/%m/%Y %H:%M:%S",      # 30/08/2025 08:00:00
        "%d/%m/%Y %H:%M",         # 30/08/2025 08:00
        "%d/%m/%Y",               # 30/08/2025
        "%B %d, %Y %H:%M:%S",     # August 30, 2025 08:00:00
        "%B %d, %Y %H:%M",        # August 30, 2025 08:00
        "%B %d, %Y",              # August 30, 2025
        "%b %d, %Y %H:%M:%S",     # Aug 30, 2025 08:00:00
        "%b %d, %Y %H:%M",        # Aug 30, 2025 08:00
        "%b %d, %Y",              # Aug 30, 2025
        "%d %B %Y %H:%M:%S",      # 30 August 2025 08:00:00
        "%d %B %Y %H:%M",         # 30 August 2025 08:00
        "%d %B %Y",               # 30 August 2025
        "%d %b %Y %H:%M:%S",      # 30 Aug 2025 08:00:00
        "%d %b %Y %H:%M",         # 30 Aug 2025 08:00
        "%d %b %Y",               # 30 Aug 2025
    ]
    
    # Time formats (to be combined with dates)
    TIME_FORMATS = [
        "%H:%M:%S",               # 08:00:00
        "%H:%M",                  # 08:00
        "%I:%M %p",               # 08:00 AM
        "%I:%M:%S %p",            # 08:00:00 AM
        "%H:%M:%S %p",            # 08:00:00 AM (24-hour with AM/PM)
    ]
    
    # Natural language patterns
    NATURAL_PATTERNS = {
        # Today/yesterday/tomorrow
        r'\b(today|yesterday|tomorrow)\b': {
            'today': 0,
            'yesterday': -1,
            'tomorrow': 1
        },
        # Now
        r'\bnow\b': 'now',
        # Relative days
        r'(\d+)\s+days?\s+(ago|from\s+now)': 'relative_days',
        # Relative weeks
        r'(\d+)\s+weeks?\s+(ago|from\s+now)': 'relative_weeks',
        # Relative months
        r'(\d+)\s+months?\s+(ago|from\s+now)': 'relative_months',
        # Relative years
        r'(\d+)\s+years?\s+(ago|from\s+now)': 'relative_years',
        # This/next/last week
        r'\b(this|next|last)\s+week\b': 'week_relative',
        # This/next/last month
        r'\b(this|next|last)\s+month\b': 'month_relative',
        # This/next/last year
        r'\b(this|next|last)\s+year\b': 'year_relative',
    }
    
    @classmethod
    def parse_datetime(cls, text: str) -> datetime:
        """
        Parse a datetime string in various formats.
        
        Args:
            text: The datetime string to parse
            
        Returns:
            Parsed datetime object
            
        Raises:
            ValueError: If the text cannot be parsed
        """
        text = text.strip()
        
        # Try natural language first
        natural_result = cls._parse_natural_language(text)
        if natural_result is not None:
            return natural_result
        
        # Try standard formats
        for fmt in cls.DATE_FORMATS:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        
        # Try combining date and time if they're separate
        combined_result = cls._try_combine_date_time(text)
        if combined_result is not None:
            return combined_result
        
        raise ValueError(f'Unable to parse datetime: "{text}"')
    
    @classmethod
    def _parse_natural_language(cls, text: str) -> Optional[datetime]:
        """Parse natural language datetime expressions."""
        text_lower = text.lower()
        now = datetime.now()
        
        # Handle "now"
        if text_lower == 'now':
            return now
        
        # Handle today/yesterday/tomorrow
        for pattern, mapping in cls.NATURAL_PATTERNS.items():
            if isinstance(mapping, dict):
                match = re.search(pattern, text_lower)
                if match:
                    day_offset = mapping[match.group(1)]
                    return now + timedelta(days=day_offset)
        
        # Handle relative days
        match = re.search(r'(\d+)\s+days?\s+(ago|from\s+now)', text_lower)
        if match:
            count = int(match.group(1))
            direction = match.group(2)
            if direction == 'ago':
                return now - timedelta(days=count)
            else:  # from now
                return now + timedelta(days=count)
        
        # Handle relative weeks
        match = re.search(r'(\d+)\s+weeks?\s+(ago|from\s+now)', text_lower)
        if match:
            count = int(match.group(1))
            direction = match.group(2)
            if direction == 'ago':
                return now - timedelta(weeks=count)
            else:  # from now
                return now + timedelta(weeks=count)
        
        # Handle relative months (approximate)
        match = re.search(r'(\d+)\s+months?\s+(ago|from\s+now)', text_lower)
        if match:
            count = int(match.group(1))
            direction = match.group(2)
            # Approximate months as 30 days
            days = count * 30
            if direction == 'ago':
                return now - timedelta(days=days)
            else:  # from now
                return now + timedelta(days=days)
        
        # Handle relative years (approximate)
        match = re.search(r'(\d+)\s+years?\s+(ago|from\s+now)', text_lower)
        if match:
            count = int(match.group(1))
            direction = match.group(2)
            # Approximate years as 365 days
            days = count * 365
            if direction == 'ago':
                return now - timedelta(days=days)
            else:  # from now
                return now + timedelta(days=days)
        
        # Handle this/next/last week
        match = re.search(r'\b(this|next|last)\s+week\b', text_lower)
        if match:
            modifier = match.group(1)
            today = now.date()
            days_since_monday = today.weekday()
            monday = today - timedelta(days=days_since_monday)
            
            if modifier == 'this':
                return datetime.combine(monday, datetime.min.time())
            elif modifier == 'next':
                return datetime.combine(monday + timedelta(days=7), datetime.min.time())
            elif modifier == 'last':
                return datetime.combine(monday - timedelta(days=7), datetime.min.time())
        
        # Handle this/next/last month
        match = re.search(r'\b(this|next|last)\s+month\b', text_lower)
        if match:
            modifier = match.group(1)
            current_month = now.month
            current_year = now.year
            
            if modifier == 'this':
                return datetime(current_year, current_month, 1)
            elif modifier == 'next':
                if current_month == 12:
                    return datetime(current_year + 1, 1, 1)
                else:
                    return datetime(current_year, current_month + 1, 1)
            elif modifier == 'last':
                if current_month == 1:
                    return datetime(current_year - 1, 12, 1)
                else:
                    return datetime(current_year, current_month - 1, 1)
        
        # Handle this/next/last year
        match = re.search(r'\b(this|next|last)\s+year\b', text_lower)
        if match:
            modifier = match.group(1)
            current_year = now.year
            
            if modifier == 'this':
                return datetime(current_year, 1, 1)
            elif modifier == 'next':
                return datetime(current_year + 1, 1, 1)
            elif modifier == 'last':
                return datetime(current_year - 1, 1, 1)
        
        return None
    
    @classmethod
    def _try_combine_date_time(cls, text: str) -> Optional[datetime]:
        """Try to combine separate date and time parts."""
        # Split by common separators
        parts = re.split(r'\s+', text.strip())
        if len(parts) < 2:
            return None
        
        # Try to find date and time parts
        date_part = None
        time_part = None
        
        for part in parts:
            # Check if it looks like a time
            if re.match(r'\d{1,2}:\d{2}(:\d{2})?(\s*[AP]M)?', part, re.IGNORECASE):
                time_part = part
            # Check if it looks like a date
            elif re.match(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\w+\s+\d{1,2},?\s+\d{4}', part, re.IGNORECASE):
                date_part = part
        
        if date_part and time_part:
            # Try to parse the combined string
            combined = f"{date_part} {time_part}"
            for fmt in cls.DATE_FORMATS:
                try:
                    return datetime.strptime(combined, fmt)
                except ValueError:
                    continue
        
        return None
    
    @classmethod
    def parse_date_time_pair(cls, date_text: str, time_text: str) -> datetime:
        """
        Parse a date and time as separate strings.
        
        Args:
            date_text: Date string (e.g., "August 30, 2025")
            time_text: Time string (e.g., "08:00 AM")
            
        Returns:
            Combined datetime object
        """
        # First try to parse as a combined string
        combined = f"{date_text} {time_text}"
        try:
            return cls.parse_datetime(combined)
        except ValueError:
            pass
        
        # Try parsing date and time separately
        date_obj = None
        time_obj = None
        
        # Parse date
        for fmt in cls.DATE_FORMATS:
            try:
                date_obj = datetime.strptime(date_text, fmt)
                break
            except ValueError:
                continue
        
        if date_obj is None:
            # Try natural language for date
            date_obj = cls._parse_natural_language(date_text)
        
        if date_obj is None:
            raise ValueError(f'Unable to parse date: "{date_text}"')
        
        # Parse time
        for fmt in cls.TIME_FORMATS:
            try:
                time_obj = datetime.strptime(time_text, fmt)
                break
            except ValueError:
                continue
        
        if time_obj is None:
            raise ValueError(f'Unable to parse time: "{time_text}"')
        
        # Combine date and time
        return datetime.combine(date_obj.date(), time_obj.time())
    
    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """Get a list of supported date/time formats."""
        formats = []
        formats.extend(cls.DATE_FORMATS)
        formats.extend([f"date + time: {fmt}" for fmt in cls.TIME_FORMATS])
        formats.extend([
            "Natural language: today, yesterday, tomorrow, now",
            "Relative: 2 days ago, next week, last month",
            "Formatted: August 30, 2025, 08/30/2025, 30/08/2025"
        ])
        return formats
