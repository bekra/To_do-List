import flet as ft
from flet import *
import json
from datetime import datetime, time
import time as time_module
from threading import Thread

class TodoApp:
    def __init__(self):
        self.tasks = []
        self.load_tasks()
        
    def load_tasks(self):
        try:
            with open('tasks.json', 'r') as file:
                self.tasks = json.load(file)
        except FileNotFoundError:
            self.tasks = []
            
    def save_tasks(self):
        with open('tasks.json', 'w') as file:
            json.dump(self.tasks, file, indent=4)

class TaskState:
    def __init__(self):
        self.selected_date = None
        self.selected_time = None

def main(page: ft.Page):
    page.adaptive = True
    page.title = "Todo List"
    page.window.width = 400
    page.window.height = 700
    page.padding = 10
    
    app = TodoApp()
    state = TaskState()
    
    # Form fields
    task_input = ft.TextField(label="Task",  width=300)
    
    # Date picker
    date_result = ft.Text()
    
    def date_picker_changed(e):
        state.selected_date = e.control.value
        date_result.value = f"Selected date: {state.selected_date.strftime('%Y-%m-%d')}"
        page.update()
    
    date_picker = ft.DatePicker(
        on_change=date_picker_changed,
        first_date=datetime.now(),
        last_date=datetime(2100, 1, 1),
    )
    
    page.overlay.append(date_picker)
    
    def open_date_picker(e):
        date_picker.open = True
        page.update()
    
    date_button = ft.ElevatedButton(
        "Pick date",
        icon=ft.icons.CALENDAR_TODAY,
        on_click=open_date_picker
    )
    
    # Time picker
    time_result = ft.Text()
    
    def time_picker_changed(e):
        state.selected_time = e.control.value
        time_result.value = f"Selected time: {state.selected_time.strftime('%H:%M')}"
        page.update()
    
    time_picker = ft.TimePicker(
        on_change=time_picker_changed,
    )
    
    page.overlay.append(time_picker)
    
    def open_time_picker(e):
        time_picker.open = True
        page.update()
    
    time_button = ft.ElevatedButton(
        "Pick time",
        icon=ft.icons.ACCESS_TIME,
        on_click=open_time_picker
    )
    
    # Task list
    tasks_column = ft.Column(scroll=ft.ScrollMode.AUTO, height=250)
    
    # Next task info
    next_task_text = ft.Text("")
    time_remaining_text = ft.Text("")
    
    def update_next_task():
        while True:
            if app.tasks:
                # Find the next upcoming task
                current_time = datetime.now()
                future_tasks = [
                    task for task in app.tasks 
                    if datetime.fromisoformat(task['date']) > current_time
                ]
                
                if future_tasks:
                    next_task = min(
                        future_tasks,
                        key=lambda x: datetime.fromisoformat(x['date'])
                    )
                    
                    # Calculate time remaining
                    time_diff = datetime.fromisoformat(next_task['date']) - current_time
                    hours = int(time_diff.total_seconds() // 3600)
                    minutes = int((time_diff.total_seconds() % 3600) // 60)
                    seconds = int(time_diff.total_seconds() % 60)
                    
                    next_task_text.value = f"Next Task: {next_task['task']}"
                    time_remaining_text.value = f"Time remaining: {hours} hours, {minutes} minutes, {seconds} seconds"
                else:
                    next_task_text.value = "No upcoming tasks"
                    time_remaining_text.value = ""
                page.update()
            
            time_module.sleep(1)
    
    # Start the timer thread
    timer_thread = Thread(target=update_next_task, daemon=True)
    timer_thread.start()
    
    def update_task_list():
        tasks_column.controls.clear()
        for i, task in enumerate(app.tasks):
            task_date = datetime.fromisoformat(task['date']).strftime('%Y-%m-%d %H:%M')
            tasks_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Row(
                                            controls=[
                                                ft.Text(task['task'], size=16, weight=ft.FontWeight.W_500),
                                            ],
                                            scroll=ft.ScrollMode.AUTO
                                        ),
                                        width=300,
                                        height=25,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text(task_date, size=12, color=ft.colors.GREY_900),
                                    ft.IconButton(
                                        icon=ft.icons.DELETE,
                                        icon_color=ft.colors.RED_500,
                                        tooltip="Delete task",
                                        on_click=lambda e, index=i: delete_task(e, index)
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.EDIT,
                                        icon_color=ft.colors.BLUE_500,
                                        tooltip="Edit task",
                                        on_click=lambda e, index=i: edit_task(e, index)
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                        ],
                    ),
                    padding=10,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=8,
                    margin=ft.margin.only(bottom=10),
                )
            )
        page.update()

    # Create alert dialog for messages
    alert_dialog = ft.AlertDialog(
        title=ft.Text("Attention"),
        on_dismiss=lambda e: print("Dialog dismissed!")
    )

    def show_message(message: str):
        alert_dialog.content = ft.Text(message)
        page.dialog = alert_dialog
        alert_dialog.open = True
        page.update()
    
    def add_task(e):
        if not task_input.value:
            show_message("Please enter a task")
            return
            
        if not state.selected_date:
            show_message("Please select a date")
            return
            
        if not state.selected_time:
            show_message("Please select a time")
            return
        
        try:
            task_datetime = datetime.combine(state.selected_date, state.selected_time)
            new_task = {
                'task': task_input.value,
                'date': task_datetime.isoformat()
            }
            app.tasks.append(new_task)
            app.save_tasks()
            
            # Clear inputs
            task_input.value = ""
            date_result.value = ""
            time_result.value = ""
            state.selected_date = None
            state.selected_time = None
            
            update_task_list()
            page.update()
        except Exception as e:
            show_message(f"Error adding task: {str(e)}")
    
    def delete_task(e, index):
        app.tasks.pop(index)
        app.save_tasks()
        update_task_list()
    
    def edit_task(e, index):
        task = app.tasks[index]
        task_datetime = datetime.fromisoformat(task['date'])
        
        task_input.value = task['task']
        state.selected_date = task_datetime.date()
        state.selected_time = task_datetime.time()
        date_result.value = f"Selected date: {state.selected_date.strftime('%Y-%m-%d')}"
        time_result.value = f"Selected time: {state.selected_time.strftime('%H:%M')}"
        
        # Remove the old task
        app.tasks.pop(index)
        app.save_tasks()
        update_task_list()
        page.update()
    
    # Build the UI
    page.add(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("To-Do Items", size=24, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            next_task_text,
                            time_remaining_text,
                        ],
                    ),
                    margin=ft.margin.symmetric(vertical=10),
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            task_input,
                            ft.Row([date_button, date_result]),
                            ft.Row([time_button, time_result]),
                            ft.ElevatedButton(
                                "Add Task",
                                icon=ft.icons.ADD,
                                on_click=add_task
                            ),
                        ],
                    ),
                    padding=20,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=8,
                    margin=ft.margin.only(bottom=20),
                ),
                tasks_column,
            ],
        )
    )
    
    # Initial update of task list
    update_task_list()

ft.app(target=main)
