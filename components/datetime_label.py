"""
DateTime Label Component.

Displays datetime values using the user's browser locale and timezone.
"""

from __future__ import annotations
from datetime import datetime
from nicegui import ui


class DateTimeLabel:
    """Label that displays datetime in user's locale and timezone."""

    @staticmethod
    def create(
        dt: datetime | None,
        format_type: str = 'datetime',
        classes: str = '',
        fallback: str = 'N/A'
    ) -> ui.label:
        """
        Create a label that displays datetime in user's local timezone and format.

        Args:
            dt: The datetime object to display (should be UTC)
            format_type: Type of formatting:
                - 'datetime': Full date and time (e.g., "Oct 31, 2025, 2:45 PM")
                - 'date': Date only (e.g., "Oct 31, 2025")
                - 'time': Time only (e.g., "2:45 PM")
                - 'full': Full verbose format (e.g., "Thursday, October 31, 2025 at 2:45:30 PM EDT")
                - 'relative': Relative time (e.g., "2 hours ago")
                - 'short': Short format (e.g., "10/31/25, 2:45 PM")
            classes: CSS classes to apply to the label
            fallback: Text to display if dt is None

        Returns:
            A NiceGUI label element
        """
        if dt is None:
            return ui.label(fallback).classes(classes)

        # Convert datetime to ISO format for JavaScript
        iso_string = dt.isoformat()

        # Format options for Intl.DateTimeFormat
        format_options = {
            'datetime': {
                'dateStyle': 'medium',
                'timeStyle': 'short',
            },
            'date': {
                'dateStyle': 'medium',
            },
            'time': {
                'timeStyle': 'short',
            },
            'full': {
                'dateStyle': 'full',
                'timeStyle': 'long',
            },
            'short': {
                'dateStyle': 'short',
                'timeStyle': 'short',
            },
        }

        # Create label
        label = ui.label('').classes(classes)
        
        # Generate JavaScript to format and set the text
        if format_type == 'relative':
            # Use relative time formatting (requires modern browsers)
            js_code = f'''
            const date = new Date('{iso_string}');
            const rtf = new Intl.RelativeTimeFormat(undefined, {{ numeric: 'auto' }});
            const diff = date - new Date();
            const seconds = Math.floor(diff / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);
            
            let text;
            if (Math.abs(days) > 0) text = rtf.format(days, 'day');
            else if (Math.abs(hours) > 0) text = rtf.format(hours, 'hour');
            else if (Math.abs(minutes) > 0) text = rtf.format(minutes, 'minute');
            else text = rtf.format(seconds, 'second');
            
            return text;
            '''
        else:
            # Use Intl.DateTimeFormat for absolute formatting
            options = format_options.get(format_type, format_options['datetime'])
            options_json = str(options).replace("'", '"')
            js_code = f'return new Intl.DateTimeFormat(undefined, {options_json}).format(new Date("{iso_string}"));'

        # Use timer to set text after element is in DOM
        async def set_text():
            result = await ui.run_javascript(f'(function() {{ {js_code} }})()', timeout=5.0)
            if result:
                label.set_text(result)
        
        ui.timer(0.1, set_text, once=True)

        return label

    @staticmethod
    def datetime(dt: datetime | None, classes: str = '', fallback: str = 'N/A') -> ui.label:
        """Create a datetime label (date and time)."""
        return DateTimeLabel.create(dt, 'datetime', classes, fallback)

    @staticmethod
    def date(dt: datetime | None, classes: str = '', fallback: str = 'N/A') -> ui.label:
        """Create a date-only label."""
        return DateTimeLabel.create(dt, 'date', classes, fallback)

    @staticmethod
    def time(dt: datetime | None, classes: str = '', fallback: str = 'N/A') -> ui.label:
        """Create a time-only label."""
        return DateTimeLabel.create(dt, 'time', classes, fallback)

    @staticmethod
    def full(dt: datetime | None, classes: str = '', fallback: str = 'N/A') -> ui.label:
        """Create a full verbose datetime label."""
        return DateTimeLabel.create(dt, 'full', classes, fallback)

    @staticmethod
    def relative(dt: datetime | None, classes: str = '', fallback: str = 'N/A') -> ui.label:
        """Create a relative time label (e.g., '2 hours ago')."""
        return DateTimeLabel.create(dt, 'relative', classes, fallback)

    @staticmethod
    def short(dt: datetime | None, classes: str = '', fallback: str = 'N/A') -> ui.label:
        """Create a short format datetime label."""
        return DateTimeLabel.create(dt, 'short', classes, fallback)
