from __future__ import annotations

import json
import shlex
import subprocess
import sys
from datetime import datetime

from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key="insecure secret key that needs to be changed"

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
        item['entry'] = parse_dt(item['entry'])
        tasks.append(item)

    return tasks


@app.route('/')
def index():
    result = subprocess.run([
        "task", "export", "next"
    ], capture_output=True)
    if result.returncode != 0:
        raise ValueError('x')

    items = parse_tasks(result.stdout)
    print(items[0])
    return render_template("index.html", data=items, relative_date=relative_date, title="Next Tasks")


@app.route('/tasks/create')
def tasks_create():
    return render_template("create-task.html", title="Create Task")


@app.route('/tasks/add', methods=['POST'])
def add_task():
    task = request.form.get('task')
    result = subprocess.run([
        "task", "add", *shlex.split(task)
    ], capture_output=True)
    if result.returncode != 0:
        raise ValueError('x')

    flash(result.stdout.decode('utf-8'))
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
