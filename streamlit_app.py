import os
from datetime import datetime
from typing import Any

import requests
import streamlit as st


API_URL = os.getenv(
    "TASKMIND_API_URL",
    "https://grand-reprieve-production-4e77.up.railway.app",
).rstrip("/")

PRIORITY_LABELS = {
    1: "Low",
    2: "Normal",
    3: "Medium",
    4: "High",
    5: "Urgent",
}


st.set_page_config(
    page_title="TaskMind AI",
    page_icon="TM",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_theme() -> None:
    st.markdown(
        """
        <style>
            :root {
                --tm-bg: #f6f7f9;
                --tm-panel: #ffffff;
                --tm-border: #d9dee7;
                --tm-text: #1d2433;
                --tm-muted: #697386;
                --tm-primary: #2563eb;
                --tm-primary-soft: #dbeafe;
                --tm-success: #168a4a;
                --tm-warning: #b7791f;
                --tm-danger: #c2410c;
            }

            .stApp {
                background: var(--tm-bg);
                color: var(--tm-text);
            }

            [data-testid="stSidebar"] {
                background: #111827;
                border-right: 1px solid #0f172a;
            }

            [data-testid="stSidebar"] * {
                color: #f9fafb;
            }

            [data-testid="stSidebar"] [data-baseweb="select"] * {
                color: #111827;
            }

            .main .block-container {
                max-width: 1240px;
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            h1, h2, h3 {
                letter-spacing: 0;
            }

            .tm-page-header {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                align-items: flex-start;
                padding: 1.25rem 0 1rem;
            }

            .tm-eyebrow {
                color: var(--tm-muted);
                font-size: 0.82rem;
                font-weight: 700;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                margin-bottom: 0.25rem;
            }

            .tm-title {
                color: var(--tm-text);
                font-size: 2.05rem;
                font-weight: 760;
                line-height: 1.1;
                margin: 0;
            }

            .tm-subtitle {
                color: var(--tm-muted);
                font-size: 1rem;
                margin-top: 0.45rem;
                max-width: 720px;
            }

            .tm-card {
                background: var(--tm-panel);
                border: 1px solid var(--tm-border);
                border-radius: 8px;
                padding: 1rem;
                box-shadow: 0 1px 2px rgba(17, 24, 39, 0.05);
            }

            .tm-task-row {
                background: var(--tm-panel);
                border: 1px solid var(--tm-border);
                border-radius: 8px;
                padding: 0.9rem 1rem;
                margin-bottom: 0.65rem;
            }

            .tm-task-row.done {
                background: #f8fafc;
            }

            .tm-task-title {
                color: var(--tm-text);
                font-size: 1rem;
                font-weight: 700;
                margin-bottom: 0.3rem;
            }

            .tm-task-row.done .tm-task-title {
                color: var(--tm-muted);
                text-decoration: line-through;
            }

            .tm-meta {
                color: var(--tm-muted);
                font-size: 0.86rem;
            }

            .tm-chip {
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                border: 1px solid var(--tm-border);
                background: #f8fafc;
                color: var(--tm-text);
                font-size: 0.78rem;
                font-weight: 700;
                line-height: 1;
                padding: 0.35rem 0.55rem;
                white-space: nowrap;
            }

            .tm-chip.high {
                border-color: #fed7aa;
                background: #fff7ed;
                color: var(--tm-danger);
            }

            .tm-chip.done {
                border-color: #bbf7d0;
                background: #f0fdf4;
                color: var(--tm-success);
            }

            .tm-empty {
                border: 1px dashed var(--tm-border);
                border-radius: 8px;
                padding: 2rem;
                text-align: center;
                color: var(--tm-muted);
                background: rgba(255, 255, 255, 0.65);
            }

            div[data-testid="stMetric"] {
                background: var(--tm-panel);
                border: 1px solid var(--tm-border);
                border-radius: 8px;
                padding: 0.85rem 1rem;
            }

            div[data-testid="stForm"] {
                background: var(--tm-panel);
                border: 1px solid var(--tm-border);
                border-radius: 8px;
                padding: 1rem;
            }

            .stButton > button,
            .stFormSubmitButton > button {
                border-radius: 6px;
                font-weight: 700;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    defaults = {
        "token": None,
        "tasks": [],
        "user_email": "",
        "last_error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def headers() -> dict[str, str]:
    if not st.session_state.token:
        return {}
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_request(method: str, path: str, **kwargs: Any) -> tuple[Any, str | None]:
    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            timeout=20,
            **kwargs,
        )
    except requests.RequestException as exc:
        return None, f"Connection error: {exc}"

    if response.status_code >= 400:
        try:
            payload = response.json()
            message = payload.get("detail") or payload.get("error") or response.text
        except ValueError:
            message = response.text
        return None, f"{response.status_code}: {message}"

    try:
        return response.json(), None
    except ValueError:
        return response.text, None


def fetch_tasks() -> None:
    data, error = api_request("GET", "/tasks", headers=headers())
    if error:
        st.session_state.last_error = error
        return
    st.session_state.tasks = data or []
    st.session_state.last_error = ""


def create_task(text: str, priority: int, due_datetime: datetime) -> str | None:
    _, error = api_request(
        "POST",
        "/task",
        json={
            "text": text,
            "priority": priority,
            "due_date": due_datetime.isoformat(),
        },
        headers={**headers(), "Content-Type": "application/json"},
    )
    if not error:
        fetch_tasks()
    return error


def update_task_completion(task_id: int, completed: bool) -> str | None:
    _, error = api_request(
        "PUT",
        f"/task/{task_id}",
        json={"completed": completed},
        headers={**headers(), "Content-Type": "application/json"},
    )
    if not error:
        fetch_tasks()
    return error


def format_due_date(value: str | None) -> str:
    if not value:
        return "No due date"
    try:
        due_date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return due_date.strftime("%d %b %Y, %H:%M")
    except ValueError:
        return value


def page_header(title: str, subtitle: str, eyebrow: str = "TaskMind AI") -> None:
    st.markdown(
        f"""
        <div class="tm-page-header">
            <div>
                <div class="tm-eyebrow">{eyebrow}</div>
                <h1 class="tm-title">{title}</h1>
                <div class="tm-subtitle">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def task_stats() -> tuple[int, int, int]:
    tasks = st.session_state.tasks
    total = len(tasks)
    done = sum(1 for task in tasks if task.get("completed"))
    open_count = total - done
    return total, open_count, done


def render_sidebar() -> str:
    st.sidebar.markdown("## TaskMind AI")
    st.sidebar.caption("AI assisted planning workspace")

    if st.session_state.token:
        menu = st.sidebar.radio(
            "Navigation",
            ["Dashboard", "Calendar", "AI Chat", "Plan"],
            label_visibility="collapsed",
        )
        st.sidebar.divider()
        st.sidebar.caption(st.session_state.user_email or "Signed in")
        if st.sidebar.button("Sign out", use_container_width=True):
            st.session_state.token = None
            st.session_state.tasks = []
            st.session_state.user_email = ""
            st.rerun()
        return menu

    menu = st.sidebar.radio(
        "Navigation",
        ["Login", "Register"],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.caption("Connected to production API")
    return menu


def render_login() -> None:
    page_header(
        "Sign in to your workspace",
        "Manage tasks, review your calendar, and let AI turn your workload into a focused plan.",
        "Welcome back",
    )

    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

        if submitted:
            if not email or not password:
                st.warning("Enter your email and password.")
            else:
                data, error = api_request(
                    "POST",
                    "/login",
                    data={"email": email, "password": password},
                )
                if error:
                    st.error(f"Login failed: {error}")
                else:
                    st.session_state.token = data["access_token"]
                    st.session_state.user_email = email
                    fetch_tasks()
                    st.success("Signed in successfully.")
                    st.rerun()

    with right:
        st.markdown(
            """
            <div class="tm-card">
                <div class="tm-eyebrow">Product focus</div>
                <h3>One clean place for planning</h3>
                <p class="tm-meta">
                    TaskMind keeps the main flow simple: add work, review the day,
                    ask AI for context, and generate a plan when the list gets noisy.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_register() -> None:
    page_header(
        "Create an account",
        "Start with a small workspace that can grow into a more complete productivity product.",
        "New workspace",
    )

    with st.form("register_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Create account", use_container_width=True)

    if submitted:
        if not email or not password:
            st.warning("Enter an email and password.")
            return

        data, error = api_request(
            "POST",
            "/register",
            data={"email": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if error:
            st.error(f"Registration failed: {error}")
        elif isinstance(data, dict) and data.get("error"):
            st.error(data["error"])
        else:
            st.success("Account created. You can sign in now.")


def render_task_row(task: dict[str, Any]) -> None:
    task_id = task["id"]
    completed = bool(task.get("completed"))
    priority = int(task.get("priority") or 3)
    priority_class = "high" if priority >= 4 else ""
    status_class = "done" if completed else ""
    status_label = "Done" if completed else "Open"

    st.markdown(
        f"""
        <div class="tm-task-row {status_class}">
            <div class="tm-task-title">{task.get("text", "Untitled task")}</div>
            <div class="tm-meta">
                {format_due_date(task.get("due_date"))}
                &nbsp;&nbsp;
                <span class="tm-chip {priority_class}">P{priority} - {PRIORITY_LABELS.get(priority, "Medium")}</span>
                &nbsp;
                <span class="tm-chip {status_class}">{status_label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    new_value = st.checkbox(
        "Completed",
        value=completed,
        key=f"completed_{task_id}_{completed}",
    )
    if new_value != completed:
        error = update_task_completion(task_id, new_value)
        if error:
            st.error(f"Could not update task: {error}")
        else:
            st.toast("Task updated.")
            st.rerun()


def render_dashboard() -> None:
    if not st.session_state.tasks:
        fetch_tasks()

    page_header(
        "Today starts from a clearer list",
        "Capture tasks quickly, keep priorities visible, and track what is already done.",
        "Dashboard",
    )

    if st.session_state.last_error:
        st.error(f"Could not load tasks: {st.session_state.last_error}")

    total, open_count, done = task_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total tasks", total)
    c2.metric("Open", open_count)
    c3.metric("Completed", done)

    st.divider()

    form_col, list_col = st.columns([0.9, 1.4], gap="large")
    with form_col:
        st.subheader("Add task")
        with st.form("add_task_form", clear_on_submit=True):
            task_input = st.text_area(
                "Task",
                placeholder="Example: Prepare the weekly planning report tomorrow at 10:00",
                height=110,
            )
            priority = st.select_slider(
                "Priority",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda value: f"P{value} - {PRIORITY_LABELS[value]}",
            )
            due_col, time_col = st.columns(2)
            due_date = due_col.date_input("Due date")
            due_time = time_col.time_input("Due time")
            submitted = st.form_submit_button("Add task", use_container_width=True)

        if submitted:
            if not task_input.strip():
                st.warning("Write a task before adding it.")
            else:
                due_datetime = datetime.combine(due_date, due_time)
                error = create_task(task_input.strip(), priority, due_datetime)
                if error:
                    st.error(f"Task could not be added: {error}")
                else:
                    st.success("Task added.")
                    st.rerun()

    with list_col:
        top_bar = st.columns([1, 0.25])
        top_bar[0].subheader("Task list")
        if top_bar[1].button("Refresh", use_container_width=True):
            fetch_tasks()
            st.rerun()

        tasks = sorted(
            st.session_state.tasks,
            key=lambda item: (
                bool(item.get("completed")),
                -(int(item.get("priority") or 3)),
                item.get("due_date") or "",
            ),
        )
        if not tasks:
            st.markdown(
                '<div class="tm-empty">No tasks yet. Add your first task on the left.</div>',
                unsafe_allow_html=True,
            )
        else:
            for task in tasks:
                render_task_row(task)


def render_calendar() -> None:
    page_header(
        "Calendar review",
        "Pick a date and review the tasks scheduled for that day.",
        "Calendar",
    )

    date_input = st.date_input("Select date", datetime.now().date())
    date_str = date_input.strftime("%Y-%m-%d")

    data, error = api_request(
        "GET",
        "/calendar",
        params={"day": date_str},
        headers=headers(),
    )
    if error:
        st.error(f"Calendar could not be loaded: {error}")
        return

    tasks = data or []
    if not tasks:
        st.markdown(
            '<div class="tm-empty">No tasks scheduled for this date.</div>',
            unsafe_allow_html=True,
        )
        return

    for task in tasks:
        render_task_row(task)


def render_ai_chat() -> None:
    page_header(
        "Ask about your workload",
        "Use natural language to summarize, prioritize, or clarify what is on your list.",
        "AI assistant",
    )

    with st.form("ai_form"):
        question = st.text_area(
            "Question",
            placeholder="What should I focus on tomorrow?",
            height=120,
        )
        submitted = st.form_submit_button("Ask AI", use_container_width=True)

    if submitted:
        if not question.strip():
            st.warning("Ask a question first.")
            return

        with st.spinner("Thinking through your tasks..."):
            data, error = api_request(
                "GET",
                "/ask",
                params={"question": question.strip()},
                headers=headers(),
            )
        if error:
            st.error(f"AI response failed: {error}")
        else:
            st.markdown(data.get("answer", "No answer received."))


def render_plan() -> None:
    page_header(
        "Tomorrow's plan",
        "Generate a focused plan from your upcoming tasks and priorities.",
        "Planning",
    )

    if st.button("Generate plan", use_container_width=False):
        with st.spinner("Building your plan..."):
            data, error = api_request("GET", "/plan", headers=headers())
        if error:
            st.error(f"Plan could not be generated: {error}")
        else:
            st.markdown(data.get("plan", "No plan generated."))


def require_auth() -> bool:
    if st.session_state.token:
        return True
    st.warning("Please sign in first.")
    return False


def main() -> None:
    inject_theme()
    init_state()
    menu = render_sidebar()

    if menu == "Login":
        render_login()
    elif menu == "Register":
        render_register()
    elif require_auth():
        if menu == "Dashboard":
            render_dashboard()
        elif menu == "Calendar":
            render_calendar()
        elif menu == "AI Chat":
            render_ai_chat()
        elif menu == "Plan":
            render_plan()


if __name__ == "__main__":
    main()
