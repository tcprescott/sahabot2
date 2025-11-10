"""
Dynamic form builder for tournament settings submission.

Renders form fields based on tournament configuration schema.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from nicegui import ui

logger = logging.getLogger(__name__)


class DynamicFormBuilder:
    """
    Builds dynamic forms based on JSON schema configuration.

    Schema format:
    {
        "fields": [
            {
                "name": "preset",
                "label": "Preset",
                "type": "select",
                "options": ["standard", "open", "inverted"],
                "required": true,
                "default": "standard"
            },
            {
                "name": "mode",
                "label": "Mode",
                "type": "text",
                "placeholder": "Enter mode",
                "required": false
            },
            {
                "name": "difficulty",
                "label": "Difficulty",
                "type": "number",
                "min": 1,
                "max": 10,
                "default": 5
            }
        ]
    }
    """

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        Initialize form builder.

        Args:
            schema: Form schema definition (JSON)
        """
        self.schema = schema or {}
        self.fields: Dict[str, Any] = {}  # Stores UI field references
        self.values: Dict[str, Any] = {}  # Stores current values

    def render(self, existing_values: Optional[Dict[str, Any]] = None) -> None:
        """
        Render the dynamic form.

        Args:
            existing_values: Pre-fill values (if updating existing submission)
        """
        if not self.schema or "fields" not in self.schema:
            # Fallback: show JSON editor if no schema configured
            ui.label(
                "No form configuration defined. Please enter settings as JSON:"
            ).classes("font-bold mb-2")
            self.fields["_json_fallback"] = (
                ui.textarea(
                    label="Settings JSON",
                    placeholder='{"preset": "standard"}',
                    value=str(existing_values) if existing_values else "{}",
                )
                .classes("w-full")
                .props("rows=10")
            )
            return

        fields_config = self.schema.get("fields", [])

        for field_config in fields_config:
            field_name = field_config.get("name")
            field_type = field_config.get("type", "text")
            field_label = field_config.get("label", field_name)
            required = field_config.get("required", False)

            # Get pre-fill value
            default_value = (
                existing_values.get(field_name)
                if existing_values
                else field_config.get("default")
            )

            # Required indicator
            label_text = f"{field_label}{'*' if required else ''}"

            # Render based on field type
            if field_type == "select":
                options = field_config.get("options", [])
                self._render_select(field_name, label_text, options, default_value)
            elif field_type == "number":
                min_val = field_config.get("min")
                max_val = field_config.get("max")
                self._render_number(
                    field_name, label_text, default_value, min_val, max_val
                )
            elif field_type == "checkbox":
                self._render_checkbox(field_name, label_text, default_value)
            elif field_type == "textarea":
                placeholder = field_config.get("placeholder", "")
                self._render_textarea(
                    field_name, label_text, default_value, placeholder
                )
            else:  # text or default
                placeholder = field_config.get("placeholder", "")
                self._render_text(field_name, label_text, default_value, placeholder)

    def _render_select(
        self, name: str, label: str, options: List[str], default: Optional[str]
    ) -> None:
        """Render select dropdown."""
        with ui.column().classes("w-full mb-4"):
            ui.label(label).classes("font-bold mb-1")
            self.fields[name] = ui.select(
                options=options,
                value=(
                    default if default in options else (options[0] if options else None)
                ),
            ).classes("w-full")

    def _render_number(
        self,
        name: str,
        label: str,
        default: Optional[float],
        min_val: Optional[float],
        max_val: Optional[float],
    ) -> None:
        """Render number input."""
        with ui.column().classes("w-full mb-4"):
            ui.label(label).classes("font-bold mb-1")
            kwargs = {}
            if min_val is not None:
                kwargs["min"] = min_val
            if max_val is not None:
                kwargs["max"] = max_val
            if default is not None:
                kwargs["value"] = default

            self.fields[name] = ui.number(label="", **kwargs).classes("w-full")

    def _render_checkbox(self, name: str, label: str, default: Optional[bool]) -> None:
        """Render checkbox."""
        with ui.row().classes("items-center mb-4"):
            self.fields[name] = ui.checkbox(
                label, value=default if default is not None else False
            )

    def _render_text(
        self, name: str, label: str, default: Optional[str], placeholder: str
    ) -> None:
        """Render text input."""
        with ui.column().classes("w-full mb-4"):
            ui.label(label).classes("font-bold mb-1")
            self.fields[name] = ui.input(
                label="", placeholder=placeholder, value=default or ""
            ).classes("w-full")

    def _render_textarea(
        self, name: str, label: str, default: Optional[str], placeholder: str
    ) -> None:
        """Render textarea."""
        with ui.column().classes("w-full mb-4"):
            ui.label(label).classes("font-bold mb-1")
            self.fields[name] = (
                ui.textarea(label="", placeholder=placeholder, value=default or "")
                .classes("w-full")
                .props("rows=3")
            )

    def get_values(self) -> Dict[str, Any]:
        """
        Get current form values.

        Returns:
            Dict of field names to values
        """
        # Handle JSON fallback mode
        if "_json_fallback" in self.fields:
            try:
                return json.loads(self.fields["_json_fallback"].value)
            except json.JSONDecodeError:
                return {}

        # Collect values from form fields
        values = {}
        for field_name, field_widget in self.fields.items():
            if hasattr(field_widget, "value"):
                values[field_name] = field_widget.value

        return values

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate form values.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Handle JSON fallback mode
        if "_json_fallback" in self.fields:
            try:
                json.loads(self.fields["_json_fallback"].value)
                return True, None
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON: {str(e)}"

        if not self.schema or "fields" not in self.schema:
            return True, None

        # Validate required fields
        for field_config in self.schema.get("fields", []):
            field_name = field_config.get("name")
            required = field_config.get("required", False)

            if required:
                value = self.fields.get(field_name)
                if value is None or (hasattr(value, "value") and not value.value):
                    field_label = field_config.get("label", field_name)
                    return False, f"{field_label} is required"

        return True, None
