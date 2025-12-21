from __future__ import annotations

import json
import subprocess
from datetime import datetime

from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tasgau - {{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: #f5f5f5;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 28px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        thead {
            background-color: #f8f9fa;
        }
        
        th {
            text-align: left;
            padding: 12px 15px;
            font-weight: 600;
            color: #555;
            border-bottom: 2px solid #dee2e6;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #dee2e6;
            color: #333;
        }
        
        tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        tbody tr:last-child td {
            border-bottom: none;
        }
        
        .id-col {
            width: 40px;
        }
        
        .age-col {
            width: 80px;
        }
        
        .project-col {
            width: 80px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Next Tasks</h1>
        <table>
            <thead>
                <tr>
                    <th class="id-col">ID</th>
                    <th class="age-col">Created</th>
                    <th class="project-col">Project</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                {% for item in data %}
                <tr>
                    <td>{{ item.id }}</td>
                    <td>{{ relative_date(item.entry) }}</td>
                    <td>{{ item.project }}</td>
                    <td>{{ item.description }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

def relative_date(dt):
    """
    Format a datetime as a relative date string.

    Args:
        dt: datetime object or string in ISO format

    Returns:
        str: Formatted relative date (e.g., "5m ago", "3d ago", "5 Oct")
    """

    now = datetime.now()
    diff = now - dt

    # Calculate total seconds
    total_seconds = diff.total_seconds()

    # Under a day: show seconds/minutes/hours
    if total_seconds < 86400:  # 86400 seconds = 1 day
        if total_seconds < 60:
            return f"{int(total_seconds)}s ago"
        elif total_seconds < 3600:
            minutes = int(total_seconds / 60)
            return f"{minutes}m ago"
        else:
            hours = int(total_seconds / 3600)
            return f"{hours}h ago"

    # Up to a week: show days
    elif total_seconds < 604800:  # 604800 seconds = 7 days
        days = int(total_seconds / 86400)
        return f"{days}d ago"

    # Over a week: show day and month name
    else:
        return dt.strftime("%-d %b").lstrip("0")


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
    return render_template_string(HTML_TEMPLATE, data=items, relative_date=relative_date, title="Next Tasks")

if __name__ == '__main__':
    app.run(debug=True)
