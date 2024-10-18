import streamlit as st
import pandas as pd
# Import plotly express module, or install it if not already available
# Import plotly express module, or install it if not already available
# try:
#     import plotly.express as plotly_express
# except ImportError:
#     try:
#         import subprocess
#         subprocess.check_call(['pip', 'install', 'plotly-express'])
#         import plotly.express as plotly_express
#     except Exception as e:
#         print("Failed to install plotly-express:", e)

import plotly.express as px
import json
import os
from datetime import datetime, date
import streamlit.components.v1 as components

# Configuration and Setup
st.set_page_config(page_title="Luki's Task Manager", page_icon="📋", layout="wide", initial_sidebar_state="expanded")

# Constants
DATA_FILE = 'Task Manager/tasks_data.json'
PRIORITY_COLORS = {'P1': '#ef4444', 'P2': '#f97316', 'P3': '#22c55e', 'ASAP': '#8b5cf6'}
COMPLETION_STAGES = {'C1': 25, 'C2': 50, 'C3': 75, 'D': 100}

# Custom CSS
def load_css():
    st.markdown("""
    <style>
        .task-card {
            background-color: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .priority-badge {
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-weight: 500;
            font-size: 0.8rem;
            text-transform: uppercase;
        }
    </style>
    """, unsafe_allow_html=True)

# Data Management
def date_serializer(obj):
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read()
                if content.strip():
                    data = json.loads(content)
                    data = pd.DataFrame(data)
                    data['Due Date'] = pd.to_datetime(data['Due Date'], errors='coerce')
                    return data
                else:
                    # File is empty
                    return pd.DataFrame(columns=['Task', 'Assigned By', 'Type', 'Location', 'Asset Class',
                                                 'Priority', 'Comments', 'Completion', 'Due Date', 'File Path'])
        except json.JSONDecodeError as e:
            st.error(f"Error loading data: {str(e)}")
            return pd.DataFrame(columns=['Task', 'Assigned By', 'Type', 'Location', 'Asset Class',
                                         'Priority', 'Comments', 'Completion', 'Due Date', 'File Path'])
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            return pd.DataFrame(columns=['Task', 'Assigned By', 'Type', 'Location', 'Asset Class',
                                         'Priority', 'Comments', 'Completion', 'Due Date', 'File Path'])
    else:
        return pd.DataFrame(columns=['Task', 'Assigned By', 'Type', 'Location', 'Asset Class',
                                     'Priority', 'Comments', 'Completion', 'Due Date', 'File Path'])

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data.to_dict('records'), f, default=date_serializer)
        return True
    except TypeError as e:
        st.error(f"Error saving data: {str(e)}")
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred while saving data: {str(e)}")
        return False
    

# Helper Functions
def get_priority_color(priority):
    return PRIORITY_COLORS.get(priority, '#6b7280')

def get_completion_percentage(completion):
    return COMPLETION_STAGES.get(completion, 0)

def get_completion_color(completion):
    percentage = get_completion_percentage(completion)
    if percentage <= 25:
        return "#ef4444"
    elif percentage <= 50:
        return "#f97316"
    elif percentage <= 75:
        return "#eab308"
    else:
        return "#22c55e"

# Validation Function
def validate_task_data(task_data):
    required_fields = ['Task', 'Assigned By', 'Type', 'Location', 'Asset Class', 'Priority', 'Completion', 'Due Date']
    for field in required_fields:
        if not task_data.get(field):
            raise ValueError(f"{field} is required")

    if task_data['Priority'] not in PRIORITY_COLORS.keys():
        raise ValueError("Invalid Priority value")

    if task_data['Completion'] not in COMPLETION_STAGES.keys():
        raise ValueError("Invalid Completion value")

    # Ensure 'Due Date' is datetime
    try:
        task_data['Due Date'] = pd.to_datetime(task_data['Due Date'], errors='coerce')
        if pd.isnull(task_data['Due Date']):
            raise ValueError("Invalid Due Date format")
    except Exception:
        raise ValueError("Invalid Due Date format")

# Task Management Functions
def add_task(task_data):
    try:
        validate_task_data(task_data)
        new_task = pd.DataFrame([task_data])
        st.session_state.tasks = pd.concat([st.session_state.tasks, new_task], ignore_index=True)
        st.session_state.tasks['Due Date'] = pd.to_datetime(st.session_state.tasks['Due Date'], errors='coerce')
        if save_data(st.session_state.tasks):
            st.success("Task added successfully!")
        else:
            st.error("Failed to save the new task.")
    except ValueError as ve:
        st.error(f"Validation error: {str(ve)}")
    except Exception as e:
        st.error(f"Error adding task: {str(e)}")

def update_task(task_index, task_data):
    try:
        validate_task_data(task_data)
        st.session_state.tasks.loc[task_index] = task_data
        st.session_state.tasks['Due Date'] = pd.to_datetime(st.session_state.tasks['Due Date'], errors='coerce')
        if save_data(st.session_state.tasks):
            st.success("Task updated successfully!")
        else:
            st.error("Failed to save the updated task.")
    except ValueError as ve:
        st.error(f"Validation error: {str(ve)}")
    except Exception as e:
        st.error(f"Error updating task: {str(e)}")

# UI Components
def render_task_form(task_data=None):
    with st.form("task_form"):
        task = st.text_input("Task Name", value=task_data['Task'] if task_data else "")
        col1, col2 = st.columns(2)
        with col1:
            assigned_by = st.text_input("Assigned By", value=task_data['Assigned By'] if task_data else "")
            task_type_options = ["Modelling", "Research", "Writing IM", "Writing OM"]
            task_type = st.selectbox("Type", task_type_options,
                                     index=task_type_options.index(task_data['Type']) if task_data and task_data['Type'] in task_type_options else 0)
            location = st.text_input("Location", value=task_data['Location'] if task_data else "")
        with col2:
            asset_class_options = ["Equity", "Debt", "Real Estate", "Other"]
            asset_class = st.selectbox("Asset Class", asset_class_options,
                                       index=asset_class_options.index(task_data['Asset Class']) if task_data and task_data['Asset Class'] in asset_class_options else 0)
            priority_options = ["P1", "P2", "P3", "ASAP"]
            priority = st.selectbox("Priority", priority_options,
                                    index=priority_options.index(task_data['Priority']) if task_data and task_data['Priority'] in priority_options else 0)
            due_date = st.date_input("Due Date", value=task_data['Due Date'].date() if task_data else date.today())
        comments = st.text_area("Comments", value=task_data['Comments'] if task_data else "")
        completion_options = ["C1", "C2", "C3", "D"]
        completion = st.select_slider("Completion", completion_options, value=task_data['Completion'] if task_data else "C1")
        file_path = st.text_input("File Path", value=task_data['File Path'] if task_data else "")

        submit_button = st.form_submit_button("Submit Task")

        if submit_button:
            return {
                'Task': task, 'Assigned By': assigned_by, 'Type': task_type,
                'Location': location, 'Asset Class': asset_class, 'Priority': priority,
                'Comments': comments, 'Completion': completion, 'Due Date': due_date,
                'File Path': file_path
            }
    return None

def render_task_list():
    if st.session_state.tasks.empty:
        st.info("No tasks to display.")
        return

    # Exclude tasks marked as 'Done'
    incomplete_tasks = st.session_state.tasks[st.session_state.tasks['Completion'] != 'D']

    if incomplete_tasks.empty:
        st.info("No incomplete tasks to display.")
        return

    for idx, task in incomplete_tasks.iterrows():
        st.markdown(f"""
        <div class="task-card">
            <h3>{task['Task']}</h3>
            <p><strong>Assigned By:</strong> {task['Assigned By']} | <strong>Type:</strong> {task['Type']} | <strong>Location:</strong> {task['Location']} | <strong>Asset Class:</strong> {task['Asset Class']}</p>
            <p><strong>Priority:</strong> <span class="priority-badge" style="background-color: {get_priority_color(task['Priority'])}; color: white;">{task['Priority']}</span></p>
            <p><strong>Comments:</strong> {task['Comments']}</p>
            <p><strong>Due Date:</strong> {task['Due Date'].strftime('%Y-%m-%d') if pd.notnull(task['Due Date']) else 'N/A'} | <strong>File Path:</strong> {task['File Path']}</p>
            <div class="completion-bar" style="background-color: #e2e8f0; height: 8px; border-radius: 4px; margin-top: 0.8rem;">
                <div style="width: {get_completion_percentage(task['Completion'])}%; height: 100%; background-color: {get_completion_color(task['Completion'])}; border-radius: 4px;"></div>
            </div>
            <p style="text-align: right; margin-top: 0.5rem;">Completion: {task['Completion']} ({get_completion_percentage(task['Completion'])}%)</p>
        </div>
        """, unsafe_allow_html=True)

def render_calendar():
    if st.session_state.tasks.empty:
        st.info("No tasks to display on the calendar.")
        return

    # Exclude tasks marked as 'Done'
    incomplete_tasks = st.session_state.tasks[st.session_state.tasks['Completion'] != 'D']
    incomplete_tasks['Due Date'] = pd.to_datetime(incomplete_tasks['Due Date'], errors='coerce')
    tasks_with_due_date = incomplete_tasks.dropna(subset=['Due Date'])

    if tasks_with_due_date.empty:
        st.info("No incomplete tasks with valid due dates to display on the calendar.")
        return

    events = [
        {
            'title': task['Task'],
            'start': task['Due Date'].strftime('%Y-%m-%d'),
            'backgroundColor': get_priority_color(task['Priority']),
            'borderColor': get_priority_color(task['Priority'])
        } for _, task in tasks_with_due_date.iterrows()
    ]

    calendar_html = f"""
    <div id='calendar'></div>
    <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.2/main.min.js'></script>
    <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.2/main.min.css' rel='stylesheet' />
    <script>
      document.addEventListener('DOMContentLoaded', function() {{
        var calendarEl = document.getElementById('calendar');
        var calendar = new FullCalendar.Calendar(calendarEl, {{
          initialView: 'dayGridMonth',
          events: {json.dumps(events)},
          headerToolbar: {{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
          }},
          height: 'auto',
          aspectRatio: 1.8
        }});
        calendar.render();
      }});
    </script>
    """
    components.html(calendar_html, height=600)

def render_summary():
    if st.session_state.tasks.empty:
        st.info("No data to display in summary.")
        return

    # Ensure 'Due Date' is datetime
    st.session_state.tasks['Due Date'] = pd.to_datetime(st.session_state.tasks['Due Date'], errors='coerce')
    tasks_with_due_date = st.session_state.tasks.dropna(subset=['Due Date'])

    st.subheader("Task Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tasks", len(st.session_state.tasks))
    with col2:
        completed_tasks = len(st.session_state.tasks[st.session_state.tasks['Completion'] == 'D'])
        st.metric("Completed Tasks", completed_tasks)
    with col3:
        current_date = pd.Timestamp.now().date()
        overdue_tasks = len(tasks_with_due_date[(tasks_with_due_date['Due Date'].dt.date < current_date) & (tasks_with_due_date['Completion'] != 'D')])
        st.metric("Overdue Tasks", overdue_tasks)
    with col4:
        upcoming_tasks = len(tasks_with_due_date[(tasks_with_due_date['Due Date'].dt.date >= current_date) & (tasks_with_due_date['Completion'] != 'D')])
        st.metric("Upcoming Tasks", upcoming_tasks)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Task Types Distribution")
        type_counts = st.session_state.tasks['Type'].value_counts()
        if not type_counts.empty:
            fig_types = px.pie(values=type_counts.values, names=type_counts.index, title="Task Types",
                               color_discrete_sequence=px.colors.qualitative.Set3)
            fig_types.update_traces(textposition='inside', textinfo='percent+label')
            fig_types.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
            st.plotly_chart(fig_types, use_container_width=True)
        else:
            st.info("No data for Task Types chart.")

    with col2:
        st.subheader("Completion Status")
        completion_data = st.session_state.tasks['Completion'].value_counts().reset_index()
        if not completion_data.empty:
            completion_data.columns = ['Status', 'Count']
            completion_data['Percentage'] = completion_data['Count'] / completion_data['Count'].sum() * 100
            fig_completion = px.bar(completion_data, x='Status', y='Count', text='Percentage', title="Task Completion Status",
                                    color='Status', color_discrete_map={'C1': '#ef4444', 'C2': '#f97316', 'C3': '#eab308', 'D': '#22c55e'})
            fig_completion.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_completion.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig_completion, use_container_width=True)
        else:
            st.info("No data for Completion Status chart.")

def completed_task():
    # Optionally, display completed tasks
    st.subheader("Completed Tasks History")
    completed_tasks_df = st.session_state.tasks[st.session_state.tasks['Completion'] == 'D']
    if not completed_tasks_df.empty:
        for idx, task in completed_tasks_df.iterrows():
            st.markdown(f"""
            <div class="task-card">
                <h3>{task['Task']}</h3>
                <p><strong>Assigned By:</strong> {task['Assigned By']} | <strong>Type:</strong> {task['Type']} | <strong>Location:</strong> {task['Location']} | <strong>Asset Class:</strong> {task['Asset Class']}</p>
                <p><strong>Priority:</strong> <span class="priority-badge" style="background-color: {get_priority_color(task['Priority'])}; color: white;">{task['Priority']}</span></p>
                <p><strong>Comments:</strong> {task['Comments']}</p>
                <p><strong>Due Date:</strong> {task['Due Date'].strftime('%Y-%m-%d') if pd.notnull(task['Due Date']) else 'N/A'} | <strong>File Path:</strong> {task['File Path']}</p>
                <p style="text-align: right; margin-top: 0.5rem;">Completed on: {task['Due Date'].strftime('%Y-%m-%d') if pd.notnull(task['Due Date']) else 'N/A'}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No completed tasks to display.")

# Main App
def main():
    load_css()
    st.title("📋 Luki's Task Manager")
    st.markdown("<p style='font-size: 1.2rem; color: #4b5563;'>Ben is just better.</p>", unsafe_allow_html=True)

    if 'tasks' not in st.session_state:
        st.session_state.tasks = load_data()

    # Sidebar
    with st.sidebar:
        st.header("Task Management")
        action = st.radio("Choose Action", ["Add New Task", "Edit Existing Task"])

        if action == "Add New Task":
            st.subheader("Add New Task")
            new_task_data = render_task_form()
            if new_task_data:
                add_task(new_task_data)

        elif action == "Edit Existing Task":
            if st.session_state.tasks.empty:
                st.info("No tasks available to edit.")
            else:
                # Exclude completed tasks from editing
                incomplete_tasks = st.session_state.tasks[st.session_state.tasks['Completion'] != 'D']
                if incomplete_tasks.empty:
                    st.info("No incomplete tasks available to edit.")
                else:
                    task_to_edit = st.selectbox("Select Task to Edit", incomplete_tasks['Task'].tolist())
                    if task_to_edit:
                        task_index = incomplete_tasks[incomplete_tasks['Task'] == task_to_edit].index[0]
                        task_data = st.session_state.tasks.loc[task_index].to_dict()
                        st.subheader(f"Edit Task: {task_to_edit}")
                        updated_task_data = render_task_form(task_data)
                        if updated_task_data:
                            update_task(task_index, updated_task_data)

    # Main Content Area
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Task List", "📅 Calendar", "📊 Summary", "✅ Completed tasks"])

    with tab1:
        st.header("Task List")
        render_task_list()

    with tab2:
        st.header("Calendar View")
        render_calendar()

    with tab3:
        st.header("Summary and Analytics")
        render_summary()

    with tab4:
        st.header("Task Completion Status")
        completed_task()

    # Footer
    st.markdown("""
    <div style='text-align: center; padding: 20px; background-color: #f0f2f6; margin-top: 30px;'>
        <p style='color: #4b5563;'>© 2024 Luki's Task Manager. All rights reserved by Ben.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
