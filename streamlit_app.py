import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Task Assistant", layout="wide")

st.title("🤖 AI Task Assistant")

# Session state
if "token" not in st.session_state:
    st.session_state.token = None
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# Sidebar for navigation
if st.session_state.token:
    menu = st.sidebar.selectbox("Menu", ["Tasks", "Calendar", "AI Chat", "Plan"])
else:
    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

# Helper function to get headers
def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

# Helper function to fetch tasks
def fetch_tasks():
    try:
        res = requests.get(f"{API_URL}/search", params={"query": ""}, headers=get_headers())
        if res.status_code == 200:
            st.session_state.tasks = res.json()
        else:
            try:
                error_data = res.json()
                error_msg = error_data.get("detail", res.text)
            except:
                error_msg = res.text
            st.error(f"Failed to fetch tasks: {res.status_code} - {error_msg}")
    except Exception as e:
        st.error(f"Error fetching tasks: {e}")

# Helper function to update task completion
def update_task_completion(completed, task_id):
    try:
        res = requests.put(
            f"{API_URL}/task/{task_id}",
            params={"completed": completed},
            headers=get_headers()
        )
        if res.status_code != 200:
            st.error(f"Failed to update task: {res.status_code}")
    except Exception as e:
        st.error(f"Error updating task: {e}")

# ---------- LOGIN ----------
if menu == "Login":
    st.subheader("🔏 Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            try:
                res = requests.post(
                    f"{API_URL}/login",
                    data={"username": email, "password": password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                data = res.json()
                if "access_token" in data:
                    st.session_state.token = data["access_token"]
                    st.success("Login successful ✅")
                    st.rerun()
                else:
                    st.error(f"Login failed: {data.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"Login error: {e}")

# ---------- REGISTER ----------
elif menu == "Register":
    st.subheader("📝 Register")

    with st.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Register")

        if submitted:
            try:
                res = requests.post(
                    f"{API_URL}/register",
                    data={"email": email, "password": password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if res.status_code == 200:
                    data = res.json()
                    if "message" in data:
                        st.success("Registration successful ✅")
                    else:
                        st.error(data.get("error", "Registration failed"))
                else:
                    try:
                        error_data = res.json()
                        error_msg = error_data.get("detail", res.text)
                    except:
                        error_msg = res.text
                    st.error(f"Registration failed: {res.status_code} - {error_msg}")
            except Exception as e:
                st.error(f"Registration error: {e}")

# ---------- TASKS ----------
elif menu == "Tasks":
    if not st.session_state.token:
        st.warning("Please login first 🔏")
        st.stop()

    st.subheader("📌 Task Manager")

    # Add task
    with st.form("add_task_form"):
        task_input = st.text_input("Add a new task")
        priority = st.selectbox("Priority", [1, 2, 3, 4, 5], index=2)  # Default 3
        due_date = st.date_input("Due Date")
        due_time = st.time_input("Due Time")
        submitted = st.form_submit_button("➕ Add Task")

        if submitted and task_input:
            # Combine date and time
            due_datetime = datetime.combine(due_date, due_time)
            try:
                res = requests.post(
                    f"{API_URL}/task",
                    json={
                        "text": task_input,
                        "priority": priority,
                        "due_date": due_datetime.isoformat()
                    },
                    headers={**get_headers(), "Content-Type": "application/json"}
                )
                if res.status_code == 200:
                    st.success("Task added successfully ✅")
                    fetch_tasks()
                else:
                    try:
                        error_data = res.json()
                        error_msg = error_data.get("detail", res.text)
                    except:
                        error_msg = res.text
                    st.error(f"Failed to add task: {res.status_code} - {error_msg}")
            except Exception as e:
                st.error(f"Error adding task: {e}")

    # Display tasks
    st.subheader("Your Tasks")
    if st.button("🔄 Refresh Tasks"):
        fetch_tasks()

    if st.session_state.tasks:
        for task in st.session_state.tasks:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**📝 {task['text']}**")
                with col2:
                    due_date = task.get('due_date')
                    if due_date:
                        st.markdown(f"📅 {due_date}")
                    else:
                        st.markdown("📅 No due date")
                with col3:
                    priority = task.get('priority', 3)
                    st.markdown(f"⚡ Priority: {priority}")
                st.divider()
    else:
        st.info("No tasks found. Add some tasks above!")

# ---------- CALENDAR ----------
elif menu == "Calendar":
    if not st.session_state.token:
        st.warning("Please login first 🔏")
        st.stop()

    st.subheader("📅 Calendar")

    date_input = st.date_input("Select a date", datetime.now().date())
    date_str = date_input.strftime("%Y-%m-%d")

    try:
        res = requests.get(
            f"{API_URL}/calendar",
            params={"day": date_str},
            headers=get_headers()
        )

        if res.status_code == 200:
            tasks = res.json()

            if tasks:
                st.subheader(f"Tasks for {date_str}")

                for task in tasks:
                    key = f"task_{task['id']}"

                    # 🔥 state yoksa initialize et
                    if key not in st.session_state:
                        st.session_state[key] = bool(task.get("completed", 0))

                    new_value = st.checkbox(
                        f"📝 {task['text']}",
                        key=key
                    )

                    # 🔥 değişim kontrolü
                    if new_value != bool(task.get("completed", 0)):
                        update_res = requests.put(
                            f"{API_URL}/task/{task['id']}",
                            json={"completed": new_value},
                            headers=get_headers()
                        )
                        st.write(update_res.text)

                        if update_res.status_code == 200:
                            st.success("Updated ✅")
                        else:
                            st.error(f"Failed: {update_res.status_code}")

            else:
                st.info("No tasks for this date")

        else:
            st.error(f"API Error: {res.status_code} - {res.text}")

    except Exception as e:
        st.error(f"Error: {e}")
        
# ---------- AI CHAT ----------
elif menu == "AI Chat":
    if not st.session_state.token:
        st.warning("Please login first 🔏")
        st.stop()

    st.subheader("🤖 AI Assistant")

    with st.form("ai_form"):
        question = st.text_input("Ask AI about your tasks")
        submitted = st.form_submit_button("❓ Ask AI")

        if submitted and question:
            try:
                res = requests.get(f"{API_URL}/ask", params={"question": question}, headers=get_headers())
                if res.status_code == 200:
                    data = res.json()
                    st.info(data.get("answer", "No answer received"))
                else:
                    try:
                        error_data = res.json()
                        error_msg = error_data.get("detail", res.text)
                    except:
                        error_msg = res.text
                    st.error(f"Failed to get AI response: {res.status_code} - {error_msg}")
            except Exception as e:
                st.error(f"Error asking AI: {e}")

# ---------- PLAN ----------
elif menu == "Plan":
    if not st.session_state.token:
        st.warning("Please login first 🔏")
        st.stop()

    st.subheader("📋 Tomorrow's Plan")

    if st.button("Generate Plan"):
        try:
            res = requests.get(f"{API_URL}/plan", headers=get_headers())
            if res.status_code == 200:
                data = res.json()
                st.markdown(data.get("plan", "No plan generated"))
            else:
                try:
                    error_data = res.json()
                    error_msg = error_data.get("detail", res.text)
                except:
                    error_msg = res.text
                st.error(f"Failed to generate plan: {res.status_code} - {error_msg}")
        except Exception as e:
            st.error(f"Error generating plan: {e}")

# Initialize tasks on app load if logged in
if st.session_state.token and menu == "Tasks" and not st.session_state.tasks:
    fetch_tasks()                              