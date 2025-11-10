"""
Reusable responsive table component.

This component renders a standard HTML table styled with the project's
`.data-table` class, and is compatible with the mobile grid layout
implemented in `static/css/responsive.css`.

Columns can either specify a `key` to render a value from each row or a
`cell_render` callable to fully control cell content. The component sets
`data-label` on each cell to support the mobile stacked layout.
"""

from __future__ import annotations
from typing import Any, Callable, Optional, Sequence
import inspect
from nicegui import ui


class TableColumn:
    """Column definition for ResponsiveTable.

    Attributes:
        label: Header label to display and to use for mobile `data-label`.
        key: Optional attribute/key name to read from a row when no renderer is provided.
        cell_render: Optional callable to render the cell. Receives the row as its single argument.
                     May be sync or async. If provided, takes precedence over `key`.
        header_classes: Optional extra classes for the header cell.
        cell_classes: Optional extra classes for body cells.
    """

    def __init__(
        self,
        label: str,
        key: Optional[str] = None,
        cell_render: Optional[Callable[[Any], Any]] = None,
        header_classes: str = "",
        cell_classes: str = "",
    ) -> None:
        self.label = label
        self.key = key
        self.cell_render = cell_render
        self.header_classes = header_classes
        self.cell_classes = cell_classes


class ResponsiveTable:
    """Responsive table that supports mobile stacked/grid layout.

    Usage:
        table = ResponsiveTable(columns=[...], rows=data)
        await table.render()
    """

    def __init__(
        self,
        columns: Sequence[TableColumn],
        rows: Sequence[Any],
        table_classes: str = "",
    ) -> None:
        self.columns = list(columns)
        self.rows = list(rows)
        self.table_classes = table_classes

    async def render(self) -> None:
        """Render the full table with header and body.

        The cells will include `data-label` attributes for mobile grid layout.
        """
        classes = f"data-table {self.table_classes}".strip()
        with ui.element("table").classes(classes).props('role="table"'):
            # Header
            with ui.element("thead").props('role="rowgroup"'):
                with ui.element("tr").props('role="row"'):
                    for col in self.columns:
                        with ui.element("th").classes(col.header_classes).props(
                            'role="columnheader" scope="col"'
                        ):
                            ui.label(col.label)

            # Body
            with ui.element("tbody").props('role="rowgroup"'):
                for row in self.rows:
                    with ui.element("tr").props('role="row"'):
                        for col in self.columns:
                            with ui.element("td").props(
                                f'data-label="{col.label}" role="cell"'
                            ).classes(col.cell_classes):
                                if col.cell_render is not None:
                                    result = col.cell_render(row)
                                    if inspect.iscoroutine(result):
                                        await result
                                elif col.key is not None:
                                    # Render from attribute or mapping key
                                    value = None
                                    if isinstance(row, dict):
                                        value = row.get(col.key)
                                    else:
                                        value = getattr(row, col.key, None)
                                    ui.label("" if value is None else str(value))
                                else:
                                    # Empty cell if neither renderer nor key provided
                                    ui.label("")
