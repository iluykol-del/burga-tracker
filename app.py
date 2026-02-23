from flask import Flask, render_template, request, redirect, make_response
import sqlite3
import os

# 🔹 Создаём объект Flask
app = Flask(__name__)

# 🔹 Для проверки, что запускается правильный файл
print("RUNNING FILE:", os.path.abspath(__file__))
print("Registered routes:", app.url_map)


# Главная страница — форма создания бага
@app.route("/")
def home():
    return render_template("form.html")

# Обработка формы
@app.route("/submit", methods=["POST"])
def submit():
    title = request.form["title"]
    description = request.form["description"]
    steps = request.form["steps"]
    expected_result = request.form["expected_result"]
    actual_result = request.form["actual_result"]
    severity = request.form["severity"]
    priority = request.form["priority"]

    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            steps TEXT NOT NULL,
            expected_result TEXT NOT NULL,
            actual_result TEXT NOT NULL,
            severity TEXT,
            priority TEXT
        )
    """)

    cursor.execute("""
        INSERT INTO bugs 
        (title, description, steps, expected_result, actual_result, severity, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, description, steps, expected_result, actual_result, severity, priority))

    conn.commit()
    conn.close()

    return redirect("/")

# Дашборд со списком багов
@app.route("/dashboard")
def dashboard():
    severity_filter = request.args.get("severity", "All")
    priority_filter = request.args.get("priority", "All")

    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()

    query = "SELECT * FROM bugs WHERE 1=1"
    params = []

    if severity_filter != "All":
        query += " AND severity = ?"
        params.append(severity_filter)
    if priority_filter != "All":
        query += " AND priority = ?"
        params.append(priority_filter)

    cursor.execute(query, params)
    bugs = cursor.fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        bugs=bugs,
        severity_filter=severity_filter,
        priority_filter=priority_filter
    )

# Очистить все баги
@app.route("/clear")
def clear_all():
    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bugs")
    conn.commit()
    conn.close()
    return redirect("/dashboard")

# Удалить один баг
@app.route("/delete/<int:bug_id>")
def delete_bug(bug_id):
    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bugs WHERE id = ?", (bug_id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

# Экспорт всех багов и статистики в HTML-файл
@app.route("/export")
def export():
    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bugs")
    bugs = cursor.fetchall()
    conn.close()

    # Начало HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Bug Report Export</title>
    </head>
    <body>
        <h1>Bug Report Export</h1>
        <table border="1" cellpadding="5">
            <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Severity</th>
                <th>Priority</th>
                <th>Description</th>
                <th>Steps</th>
                <th>Expected</th>
                <th>Actual</th>
            </tr>
    """

    # Добавляем строки для каждого бага
    for bug in bugs:
        html += f"""
            <tr>
                <td>{bug[0]}</td>
                <td>{bug[1]}</td>
                <td>{bug[6]}</td>
                <td>{bug[7]}</td>
                <td>{bug[2]}</td>
                <td>{bug[3]}</td>
                <td>{bug[4]}</td>
                <td>{bug[5]}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    # Скачивание файла
    from flask import Response
    return Response(
        html,
        mimetype="text/html",
        headers={"Content-Disposition":"attachment;filename=bug_report.html"}
    )
# 🔹 Старт сервера
if __name__ == "__main__":
    app.run(debug=True)