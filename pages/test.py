"""
Test page for SahaBot2 - Available only in DEBUG mode.

This page displays examples of all custom components and NiceGUI UI elements
to make it easier to test CSS changes and ensure consistent styling.
"""
from datetime import datetime, timezone
from nicegui import ui
from components.base_page import BasePage
from components.card import Card
from components.data_table import ResponsiveTable, TableColumn
from components.datetime_label import DateTimeLabel
from config import settings


def register():
    """Register test page routes (only if DEBUG is enabled)."""
    if not settings.DEBUG:
        return  # Don't register the page in production

    @ui.page('/test')
    async def test_page():
        """Test page showing all components and UI elements."""
        base = BasePage.authenticated_page(title="SahaBot2 - Test Page")

        async def content(page: BasePage):
            """Render test page content."""
            # Warning banner
            with ui.element('div').classes('card bg-warning'):
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('items-center gap-md'):
                        ui.icon('warning').classes('icon-large')
                        with ui.column().classes('gap-sm'):
                            ui.label('Test Page - DEBUG Mode Only').classes('text-xl font-bold')
                            ui.label('This page displays examples of all components and UI elements for CSS testing.')

            # Typography Section
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Typography').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label('Heading 1').classes('text-3xl font-bold mb-2')
                    ui.label('Heading 2').classes('text-2xl font-bold mb-2')
                    ui.label('Heading 3').classes('text-xl font-bold mb-2')
                    ui.label('Regular text - The quick brown fox jumps over the lazy dog')
                    ui.label('Bold text - The quick brown fox jumps over the lazy dog').classes('font-bold')
                    ui.label('Italic text - The quick brown fox jumps over the lazy dog').classes('italic')
                    ui.label('Small text - The quick brown fox jumps over the lazy dog').classes('text-sm')
                    ui.label('Large text - The quick brown fox jumps over the lazy dog').classes('text-lg')

            # Buttons Section
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Buttons').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('gap-md flex-wrap'):
                        ui.button('Default Button', on_click=lambda: ui.notify('Button clicked!')).classes('btn')
                        ui.button('Primary Button', on_click=lambda: ui.notify('Primary clicked!')).classes('btn btn-primary')
                        ui.button('Secondary Button', on_click=lambda: ui.notify('Secondary clicked!')).classes('btn btn-secondary')
                        ui.button('Danger Button', on_click=lambda: ui.notify('Danger clicked!')).classes('btn btn-danger')
                        ui.button('Success Button', on_click=lambda: ui.notify('Success clicked!')).classes('btn btn-success')
                        ui.button('Warning Button', on_click=lambda: ui.notify('Warning clicked!')).classes('btn btn-warning')
                    with ui.row().classes('gap-md flex-wrap mt-4'):
                        ui.button('Disabled Button', on_click=lambda: ui.notify('Should not see this')).props('disabled').classes('btn')
                        ui.button('Icon Button', icon='star', on_click=lambda: ui.notify('Icon button!')).classes('btn btn-primary')
                        ui.button('Loading Button', on_click=lambda: ui.notify('Loading...')).props('loading').classes('btn')

            # Badges Section
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Badges').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('gap-md flex-wrap items-center'):
                        ui.badge('Default Badge').classes('badge')
                        ui.badge('Success').classes('badge badge-success')
                        ui.badge('Warning').classes('badge badge-warning')
                        ui.badge('Error').classes('badge badge-error')
                        ui.badge('Info').classes('badge badge-info')
                        ui.badge('Admin').classes('badge badge-admin')
                        ui.badge('Primary').classes('badge badge-primary')

            # Input Elements Section
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Input Elements').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label('Text Input').classes('font-bold mb-2')
                    ui.input(label='Username', placeholder='Enter username', value='').classes('w-full')

                    ui.label('Textarea').classes('font-bold mb-2 mt-4')
                    ui.textarea(label='Description', placeholder='Enter description').classes('w-full')

                    ui.label('Number Input').classes('font-bold mb-2 mt-4')
                    ui.number(label='Age', value=25, min=0, max=120).classes('w-full')

                    ui.label('Select').classes('font-bold mb-2 mt-4')
                    ui.select(
                        label='Choose an option',
                        options=['Option 1', 'Option 2', 'Option 3'],
                        value='Option 1'
                    ).classes('w-full')

                    ui.label('Checkbox').classes('font-bold mb-2 mt-4')
                    with ui.column().classes('gap-sm'):
                        ui.checkbox('Option 1', value=True)
                        ui.checkbox('Option 2', value=False)
                        ui.checkbox('Option 3', value=False)

                    ui.label('Radio Buttons').classes('font-bold mb-2 mt-4')
                    ui.radio(['Option A', 'Option B', 'Option C'], value='Option A').classes('gap-sm')

                    ui.label('Switch').classes('font-bold mb-2 mt-4')
                    ui.switch('Enable feature', value=True)

                    ui.label('Slider').classes('font-bold mb-2 mt-4')
                    ui.slider(min=0, max=100, value=50).classes('w-full')

                    ui.label('Toggle').classes('font-bold mb-2 mt-4')
                    ui.toggle(['Left', 'Center', 'Right'], value='Center')

                    ui.label('Color Picker').classes('font-bold mb-2 mt-4')
                    ui.color_picker(label='Choose color', value='#3b82f6')

                    ui.label('Date Input').classes('font-bold mb-2 mt-4')
                    ui.date(value='2025-11-06').classes('w-full')

                    ui.label('Time Input').classes('font-bold mb-2 mt-4')
                    ui.time(value='12:00').classes('w-full')

            # Card Component Examples
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Card Components').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('gap-md flex-wrap'):
                        with ui.column().classes('gap-md').style('flex: 1; min-width: 300px;'):
                            Card.simple('Simple Card', 'This is a simple card with a title and description')
                            Card.info('Info Card', [
                                ('Label 1', 'Value 1'),
                                ('Label 2', 'Value 2'),
                                ('Label 3', 'Value 3'),
                            ])
                        with ui.column().classes('gap-md').style('flex: 1; min-width: 300px;'):
                            Card.action(
                                'Action Card',
                                'This card has an action button',
                                'Click Me',
                                lambda: ui.notify('Action card button clicked!')
                            )

            # DateTimeLabel Component
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('DateTimeLabel Component').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    now = datetime.now(timezone.utc)
                    ui.label('Current Time Examples:').classes('font-bold mb-2')
                    with ui.column().classes('gap-sm'):
                        with ui.row().classes('gap-md items-center'):
                            ui.label('Relative:').classes('w-32')
                            DateTimeLabel.create(now, format_type='relative')
                        with ui.row().classes('gap-md items-center'):
                            ui.label('DateTime:').classes('w-32')
                            DateTimeLabel.create(now, format_type='datetime')
                        with ui.row().classes('gap-md items-center'):
                            ui.label('Date:').classes('w-32')
                            DateTimeLabel.create(now, format_type='date')
                        with ui.row().classes('gap-md items-center'):
                            ui.label('Time:').classes('w-32')
                            DateTimeLabel.create(now, format_type='time')
                        with ui.row().classes('gap-md items-center'):
                            ui.label('Full:').classes('w-32')
                            DateTimeLabel.create(now, format_type='full')
                        with ui.row().classes('gap-md items-center'):
                            ui.label('Short:').classes('w-32')
                            DateTimeLabel.create(now, format_type='short')

            # ResponsiveTable Component
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('ResponsiveTable Component').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    # Sample data
                    sample_data = [
                        {'name': 'Alice', 'role': 'Admin', 'status': 'Active', 'score': 95},
                        {'name': 'Bob', 'role': 'User', 'status': 'Active', 'score': 82},
                        {'name': 'Charlie', 'role': 'Moderator', 'status': 'Inactive', 'score': 78},
                        {'name': 'Diana', 'role': 'User', 'status': 'Active', 'score': 91},
                    ]

                    columns = [
                        TableColumn(label='Name', key='name'),
                        TableColumn(label='Role', key='role'),
                        TableColumn(label='Status', cell_render=lambda row: ui.badge(row['status']).classes(
                            'badge-success' if row['status'] == 'Active' else 'badge-error'
                        )),
                        TableColumn(label='Score', key='score'),
                    ]

                    table = ResponsiveTable(columns=columns, rows=sample_data)
                    await table.render()

            # Layout Examples
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Layout Examples').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label('Row Layout').classes('font-bold mb-2')
                    with ui.row().classes('gap-md'):
                        with ui.element('div').classes('card').style('padding: 1rem; flex: 1;'):
                            ui.label('Item 1')
                        with ui.element('div').classes('card').style('padding: 1rem; flex: 1;'):
                            ui.label('Item 2')
                        with ui.element('div').classes('card').style('padding: 1rem; flex: 1;'):
                            ui.label('Item 3')

                    ui.label('Column Layout').classes('font-bold mb-2 mt-4')
                    with ui.column().classes('gap-md'):
                        with ui.element('div').classes('card').style('padding: 1rem;'):
                            ui.label('Item A')
                        with ui.element('div').classes('card').style('padding: 1rem;'):
                            ui.label('Item B')
                        with ui.element('div').classes('card').style('padding: 1rem;'):
                            ui.label('Item C')

                    ui.label('Grid Layout').classes('font-bold mb-2 mt-4')
                    with ui.element('div').style('display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;'):
                        for i in range(6):
                            with ui.element('div').classes('card').style('padding: 1rem;'):
                                ui.label(f'Grid Item {i+1}')

            # Icons
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Material Icons').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('gap-md flex-wrap'):
                        for icon in ['home', 'person', 'settings', 'favorite', 'star', 'info', 'warning', 'error', 'check_circle', 'delete', 'edit', 'search', 'menu', 'close', 'add', 'remove']:
                            with ui.column().classes('items-center gap-sm'):
                                ui.icon(icon).classes('icon-large')
                                ui.label(icon).classes('text-sm')

            # Notifications
            with ui.element('div').classes('card mt-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Notifications').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    with ui.row().classes('gap-md flex-wrap'):
                        ui.button('Success Notification', on_click=lambda: ui.notify('Success!', type='positive')).classes('btn btn-success')
                        ui.button('Error Notification', on_click=lambda: ui.notify('Error!', type='negative')).classes('btn btn-danger')
                        ui.button('Warning Notification', on_click=lambda: ui.notify('Warning!', type='warning')).classes('btn btn-warning')
                        ui.button('Info Notification', on_click=lambda: ui.notify('Info!', type='info')).classes('btn')

            # Separators
            with ui.element('div').classes('card mt-4 mb-4'):
                with ui.element('div').classes('card-header'):
                    ui.label('Separators').classes('text-2xl font-bold')
                with ui.element('div').classes('card-body'):
                    ui.label('Content before separator')
                    ui.separator()
                    ui.label('Content after separator')

        # Sidebar
        sidebar_items = [
            base.create_nav_link('Home', 'home', '/'),
            base.create_separator(),
            base.create_nav_link('Test Page', 'science', '/test'),
        ]

        await base.render(content, sidebar_items)
