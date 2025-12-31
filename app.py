from __future__ import annotations

import json
import shlex
import subprocess
import sys
from datetime import datetime
from logging.config import dictConfig

from flask import Flask, render_template, request, flash, redirect, url_for

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)
app.secret_key="insecure secret key that needs to be changed"

logger = app.logger

class TaskCommand:
    """Represents a command to be run."""

    def __init__(
        self,
        command: str,
        filter: list[str] | None = None,
        mods: list[str] | None = None
    ):
        self.command = command
        """The actual command name, e.g 'add' or 'modify'"""

        self.filter = filter
        """The filter(s) to apply to a command."""

        self.mods = mods
        """The mods to apply to a command."""

    def run(self):
        """Run the specified command."""

        args = [
            "task",
            *(self.filter or []),
            self.command,
            *(self.mods or []),
        ]

        logger.info(f"Running command: %r", args)
        result = subprocess.run(args, capture_output=True)
        if result.returncode != 0:
            logger.error(
                "Command exited with code %r\n%s",
                result.returncode,
                result.stderr.decode("utf-8"),
            )
            raise RuntimeError(f'task command exited with code {result.returncode}')

        return result.stdout


class Task:
    """Represents a task object."""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    def __getattr__(self, key):
        if key not in self.data:
            raise AttributeError(key)

        return self.data[key]

    @classmethod
    def parse(cls, data):
        logger.info("%r", data)
        data['entry'] = parse_dt(data['entry'])
        return cls(data)


def relative_date(dt):
    """Format a datetime as a relative date string."""

    now = datetime.now()
    total_seconds = (now - dt).total_seconds()

    if total_seconds < 86400:
        if total_seconds < 60:
            return f"{int(total_seconds)}s ago"
        elif total_seconds < 3600:
            minutes = int(total_seconds / 60)
            return f"{minutes}m ago"
        else:
            hours = int(total_seconds / 3600)
            return f"{hours}h ago"

    elif total_seconds < 604800:
        days = int(total_seconds / 86400)
        return f"{days}d ago"

    else:
        return dt.strftime("%-d %b")


def parse_dt(timestamp: str) -> datetime:
    date, time = timestamp.split('T')
    return datetime(
        year=int(date[:4]),
        month=int(date[4:6]),
        day=int(date[6:8]),
        hour=int(time[:2]),
        minute=int(time[2:4]),
        second=int(time[4:6]),
    )


def parse_tasks(data: bytes):
    tasks = []
    for item in json.loads(data):
        task = Task.parse(item)
        tasks.append(task)

    return tasks


@app.route('/')
def index():

    report = request.args.get("report", "next")
    query = request.args.get("query", "")

    logger.info("Query: %r", query)
    command = TaskCommand("export", filter=shlex.split(query), mods=[report])

    items = parse_tasks(command.run())
    return render_template(
        "index.html",
        data=items,
        relative_date=relative_date,
        report=report,
        query=query,
        title=f"{report.capitalize()} Tasks",
    )


@app.route('/task/<task_id>')
def task_info(task_id):
    """Show detailed information about a task"""
    command = TaskCommand("info", filter=[str(task_id)])
    result = command.run().decode("utf-8")

    return render_template("task-info.html", info=result, title=f"Task {task_id}")


@app.route('/tasks/create')
def tasks_create():
    return render_template("create-task.html", title="Create Task")


@app.route('/tasks/complete', methods=['PUT'])
def tasks_complete():
    """Mark the given tasks as complete."""
    task_ids = [int(t) for t in request.form.getlist("selected_task_ids")]

    command = TaskCommand("done", filter=[",".join(str(t) for t in task_ids)])
    result = command.run()
    flash(result.decode("utf-8"))

    command = TaskCommand("export", mods=["next"])
    items = parse_tasks(command.run())
    return render_template("index.html", data=items, relative_date=relative_date, title="Next Tasks")


@app.route('/tasks/add', methods=['POST'])
def add_task():
    task = request.form.get('task')

    command = TaskCommand("add", mods=shlex.split(task))
    result = command.run()
    flash(result.decode('utf-8'))

    return redirect(url_for('index'))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format="[%(levelName)s]: %(message)s")
    app.run(debug=True)
