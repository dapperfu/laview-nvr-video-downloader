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
        "%B %d, %Y %I:%M %p",     # August 30, 2025 08:00 AM
        "%B %d, %Y %I:%M:%S %p",  # August 30, 2025 08:00:00 AM
        "%B %d, %Y",              # August 30, 2025
        "%b %d, %Y %H:%M:%S",     # Aug 30, 2025 08:00:00
        "%b %d, %Y %H:%M",        # Aug 30, 2025 08:00
        "%b %d, %Y %I:%M %p",     # Aug 30, 2025 08:00 AM
        "%b %d, %Y %I:%M:%S %p",  # Aug 30, 2025 08:00:00 AM
        "%b %d, %Y",              # Aug 30, 2025
        "%d %B %Y %H:%M:%S",      # 30 August 2025 08:00:00
        "%d %B %Y %H:%M",         # 30 August 2025 08:00
        "%d %B %Y %I:%M %p",      # 30 August 2025 08:00 AM
        "%d %B %Y %I:%M:%S %p",   # 30 August 2025 08:00:00 AM
        "%d %B %Y",               # 30 August 2025
        "%d %b %Y %H:%M:%S",      # 30 Aug 2025 08:00:00
        "%d %b %Y %H:%M",         # 30 Aug 2025 08:00
        "%d %b %Y %I:%M %p",      # 30 Aug 2025 08:00 AM
        "%d %b %Y %I:%M:%S %p",   # 30 Aug 2025 08:00:00 AM
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
        
        # Try parsing combined natural language with time first (more specific)
        combined_natural_result = cls._parse_combined_natural_language(text)
        if combined_natural_result is not None:
            return combined_natural_result
        
        # Try natural language
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

    @classmethod
    def _parse_combined_natural_language(cls, text: str) -> Optional[datetime]:
        """Parse combined natural language like '8 AM yesterday' or 'yesterday 8 AM'."""
        text_lower = text.lower()
        now = datetime.now()
        
        # Patterns for time + natural language
        time_natural_patterns = [
            # "8 AM yesterday", "2:30 PM today", "6:00 AM tomorrow"
            (r'(\d{1,2}:\d{2}(:\d{2})?\s*[ap]m)\s+(today|yesterday|tomorrow)', 'time_natural'),
            # "8 AM 2 days ago", "2:30 PM next week"
            (r'(\d{1,2}:\d{2}(:\d{2})?\s*[ap]m)\s+(\d+)\s+(days?|weeks?|months?|years?)\s+(ago|from\s+now)', 'time_relative'),
            # "8 AM this week", "2:30 PM last month"
            (r'(\d{1,2}:\d{2}(:\d{2})?\s*[ap]m)\s+(this|next|last)\s+(week|month|year)', 'time_period'),
        ]
        
        # Patterns for natural language + time
        natural_time_patterns = [
            # "yesterday 8 AM", "today 2:30 PM", "tomorrow 6:00 AM"
            (r'(today|yesterday|tomorrow)\s+(\d{1,2}:\d{2}(:\d{2})?\s*[ap]m)', 'natural_time'),
            # "2 days ago 8 AM", "next week 2:30 PM"
            (r'(\d+)\s+(days?|weeks?|months?|years?)\s+(ago|from\s+now)\s+(\d{1,2}:\d{2}(:\d{2})?\s*[ap]m)', 'relative_time'),
            # "this week 8 AM", "last month 2:30 PM"
            (r'(this|next|last)\s+(week|month|year)\s+(\d{1,2}:\d{2}(:\d{2})?\s*[ap]m)', 'period_time'),
        ]
        
        # Try time + natural language patterns
        for pattern, pattern_type in time_natural_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if pattern_type == 'time_natural':
                    time_str = match.group(1)
                    natural = match.group(3)
                    
                    # Parse the time
                    time_obj = cls._parse_time_string(time_str)
                    if time_obj is None:
                        continue
                    
                    # Get the base date
                    if natural == 'today':
                        base_date = now.date()
                    elif natural == 'yesterday':
                        base_date = (now - timedelta(days=1)).date()
                    elif natural == 'tomorrow':
                        base_date = (now + timedelta(days=1)).date()
                    else:
                        continue
                    
                    return datetime.combine(base_date, time_obj)
                
                elif pattern_type == 'time_relative':
                    time_str = match.group(1)
                    count = int(match.group(3))
                    unit = match.group(4)
                    direction = match.group(5)
                    
                    # Parse the time
                    time_obj = cls._parse_time_string(time_str)
                    if time_obj is None:
                        continue
                    
                    # Calculate the base date
                    if unit == 'days':
                        delta = timedelta(days=count)
                    elif unit == 'weeks':
                        delta = timedelta(weeks=count)
                    elif unit == 'months':
                        delta = timedelta(days=count * 30)  # Approximate
                    elif unit == 'years':
                        delta = timedelta(days=count * 365)  # Approximate
                    else:
                        continue
                    
                    if direction == 'ago':
                        base_date = (now - delta).date()
                    else:  # from now
                        base_date = (now + delta).date()
                    
                    return datetime.combine(base_date, time_obj)
                
                elif pattern_type == 'time_period':
                    time_str = match.group(1)
                    modifier = match.group(3)
                    period = match.group(4)
                    
                    # Parse the time
                    time_obj = cls._parse_time_string(time_str)
                    if time_obj is None:
                        continue
                    
                    # Calculate the base date based on period
                    if period == 'week':
                        today = now.date()
                        days_since_monday = today.weekday()
                        monday = today - timedelta(days=days_since_monday)
                        
                        if modifier == 'this':
                            base_date = monday
                        elif modifier == 'next':
                            base_date = monday + timedelta(days=7)
                        elif modifier == 'last':
                            base_date = monday - timedelta(days=7)
                        else:
                            continue
                    
                    elif period == 'month':
                        current_month = now.month
                        current_year = now.year
                        
                        if modifier == 'this':
                            base_date = datetime(current_year, current_month, 1).date()
                        elif modifier == 'next':
                            if current_month == 12:
                                base_date = datetime(current_year + 1, 1, 1).date()
                            else:
                                base_date = datetime(current_year, current_month + 1, 1).date()
                        elif modifier == 'last':
                            if current_month == 1:
                                base_date = datetime(current_year - 1, 12, 1).date()
                            else:
                                base_date = datetime(current_year, current_month - 1, 1).date()
                        else:
                            continue
                    
                    elif period == 'year':
                        current_year = now.year
                        
                        if modifier == 'this':
                            base_date = datetime(current_year, 1, 1).date()
                        elif modifier == 'next':
                            base_date = datetime(current_year + 1, 1, 1).date()
                        elif modifier == 'last':
                            base_date = datetime(current_year - 1, 1, 1).date()
                        else:
                            continue
                    else:
                        continue
                    
                    return datetime.combine(base_date, time_obj)
        
        # Try natural language + time patterns
        for pattern, pattern_type in natural_time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if pattern_type == 'natural_time':
                    natural = match.group(1)
                    time_str = match.group(2)
                    
                    # Parse the time
                    time_obj = cls._parse_time_string(time_str)
                    if time_obj is None:
                        continue
                    
                    # Get the base date
                    if natural == 'today':
                        base_date = now.date()
                    elif natural == 'yesterday':
                        base_date = (now - timedelta(days=1)).date()
                    elif natural == 'tomorrow':
                        base_date = (now + timedelta(days=1)).date()
                    else:
                        continue
                    
                    return datetime.combine(base_date, time_obj)
                
                elif pattern_type == 'relative_time':
                    count = int(match.group(1))
                    unit = match.group(2)
                    direction = match.group(3)
                    time_str = match.group(4)
                    
                    # Parse the time
                    time_obj = cls._parse_time_string(time_str)
                    if time_obj is None:
                        continue
                    
                    # Calculate the base date
                    if unit == 'days':
                        delta = timedelta(days=count)
                    elif unit == 'weeks':
                        delta = timedelta(weeks=count)
                    elif unit == 'months':
                        delta = timedelta(days=count * 30)  # Approximate
                    elif unit == 'years':
                        delta = timedelta(days=count * 365)  # Approximate
                    else:
                        continue
                    
                    if direction == 'ago':
                        base_date = (now - delta).date()
                    else:  # from now
                        base_date = (now + delta).date()
                    
                    return datetime.combine(base_date, time_obj)
                
                elif pattern_type == 'period_time':
                    modifier = match.group(1)
                    period = match.group(2)
                    time_str = match.group(3)
                    
                    # Parse the time
                    time_obj = cls._parse_time_string(time_str)
                    if time_obj is None:
                        continue
                    
                    # Calculate the base date based on period
                    if period == 'week':
                        today = now.date()
                        days_since_monday = today.weekday()
                        monday = today - timedelta(days=days_since_monday)
                        
                        if modifier == 'this':
                            base_date = monday
                        elif modifier == 'next':
                            base_date = monday + timedelta(days=7)
                        elif modifier == 'last':
                            base_date = monday - timedelta(days=7)
                        else:
                            continue
                    
                    elif period == 'month':
                        current_month = now.month
                        current_year = now.year
                        
                        if modifier == 'this':
                            base_date = datetime(current_year, current_month, 1).date()
                        elif modifier == 'next':
                            if current_month == 12:
                                base_date = datetime(current_year + 1, 1, 1).date()
                            else:
                                base_date = datetime(current_year, current_month + 1, 1).date()
                        elif modifier == 'last':
                            if current_month == 1:
                                base_date = datetime(current_year - 1, 12, 1).date()
                            else:
                                base_date = datetime(current_year, current_month - 1, 1).date()
                        else:
                            continue
                    
                    elif period == 'year':
                        current_year = now.year
                        
                        if modifier == 'this':
                            base_date = datetime(current_year, 1, 1).date()
                        elif modifier == 'next':
                            base_date = datetime(current_year + 1, 1, 1).date()
                        elif modifier == 'last':
                            base_date = datetime(current_year - 1, 1, 1).date()
                        else:
                            continue
                    else:
                        continue
                    
                    return datetime.combine(base_date, time_obj)
        
        return None
    
    @classmethod
    def _parse_time_string(cls, time_str: str) -> Optional[datetime.time]:
        """Parse a time string into a time object."""
        # Normalize the time string to handle variations in AM/PM formatting
        normalized_time = time_str.strip()
        
        # If it has AM/PM but no space, add a space
        if re.search(r'\d+:\d+(:\d+)?[ap]m', normalized_time, re.IGNORECASE):
            normalized_time = re.sub(r'([ap]m)', r' \1', normalized_time, flags=re.IGNORECASE)
        
        for fmt in cls.TIME_FORMATS:
            try:
                time_obj = datetime.strptime(normalized_time, fmt)
                return time_obj.time()
            except ValueError:
                continue
        return None
