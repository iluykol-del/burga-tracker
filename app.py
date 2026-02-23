from flask import Flask, render_template, request, redirect
import sqlite3
import os
print("RUNNING FILE:", os.path.abspath(__file__))
print("Registered routes:", app.url_map)

app = Flask(__name__)

# 🔹 Для проверки, что запускается правильный файл
print("RUNNING FILE:", __file__)
print(app.url_map)

# Главная страница — форма создания бага
@app.route("/")
def home():
    return render_template("form.html")

# Обработка формы
@app.route("/submit", methods=["POST"])
def submit():
    title = request.form["title"]
    description = request.form["description"]
    severity = request.form["severity"]
    priority = request.form["priority"]

    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT,
            priority TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO bugs (title, description, severity, priority)
        VALUES (?, ?, ?, ?)
    """, (title, description, severity, priority))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

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

# 🔹 Старт сервера
if __name__ == "__main__":
    app.run(debug=True)