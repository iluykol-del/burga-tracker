from flask import Flask, render_template, request, redirect, make_response, send_file
import sqlite3
import os
import pdfkit
from io import BytesIO
# 🔹 Создаём объект Flask
app = Flask(__name__)

# 🔹 Для проверки, что запускается правильный файл
print("RUNNING FILE:", os.path.abspath(__file__))
print("Registered routes:", app.url_map)

# 🔹 Подключение к SQLite и проверка структуры таблицы
def init_db():
    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()

    # Создаём таблицу, если её нет
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT,
            priority TEXT
        )
    """)

    # Добавляем недостающие колонки (без удаления старых данных)
    # Используем try/except чтобы не было ошибки, если колонка уже есть
    for column, col_type in [("steps", "TEXT"), ("expected", "TEXT"), ("actual", "TEXT")]:
        try:
            cursor.execute(f"ALTER TABLE bugs ADD COLUMN {column} {col_type}")
        except sqlite3.OperationalError:
            # Колонка уже существует
            pass

    conn.commit()
    conn.close()

# 🔹 В начале app.py вызываем инициализацию базы
init_db()


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

    # Удаляем все баги
    cursor.execute("DELETE FROM bugs")
    # Сбрасываем счетчик AUTOINCREMENT
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='bugs'")

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

# Форма редактирования бага
@app.route("/edit/<int:bug_id>", methods=["GET", "POST"])
def edit_bug(bug_id):
    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()

    if request.method == "POST":
        # Получаем данные из формы редактирования
        title = request.form["title"]
        description = request.form["description"]
        steps = request.form["steps"]
        expected = request.form["expected"]
        actual = request.form["actual"]
        severity = request.form["severity"]
        priority = request.form["priority"]

        # Обновляем запись в базе
        cursor.execute("""
            UPDATE bugs
            SET title = ?, description = ?, steps = ?, expected = ?, actual = ?, severity = ?, priority = ?
            WHERE id = ?
        """, (title, description, steps, expected, actual, severity, priority, bug_id))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    # GET-запрос — показываем форму с текущими данными
    cursor.execute("SELECT * FROM bugs WHERE id = ?", (bug_id,))
    bug = cursor.fetchone()
    conn.close()

    return render_template("edit.html", bug=bug)


    # Формируем статистику по комбинации Severity + Priority
    
@app.route("/export")
def export():
    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bugs")
    bugs = cursor.fetchall()
    conn.close()

    # 🔹 Формируем статистику по комбинации Severity + Priority
    stats = {}
    for bug in bugs:
        key = f"{bug[6]} {bug[7]}"  # bug[6]=Severity, bug[7]=Priority
        stats[key] = stats.get(key, 0) + 1

    # 🔹 Генерируем HTML
    html = "<h2>Bug Report</h2>"

    html += "<h3>Statistics</h3><ul>"
    for key, count in stats.items():
        html += f"<li>{key}: {count}</li>"
    html += "</ul>"

    html += "<table border='1'>"
    html += "<tr><th>ID</th><th>Title</th><th>Severity</th><th>Priority</th><th>Description</th>"
    html += "<th>Steps</th><th>Expected</th><th>Actual</th></tr>"

    for bug in bugs:
        html += "<tr>"
        html += f"<td>{bug[0]}</td>"  # ID
        html += f"<td>{bug[1]}</td>"  # Title
        html += f"<td>{bug[6]}</td>"  # Severity
        html += f"<td>{bug[7]}</td>"  # Priority
        html += f"<td>{bug[2]}</td>"  # Description
        html += f"<td>{bug[3]}</td>"  # Steps
        html += f"<td>{bug[4]}</td>"  # Expected
        html += f"<td>{bug[5]}</td>"  # Actual
        html += "</tr>"

    html += "</table>"

    # 🔹 Создаём in-memory файл для скачивания
    buffer = BytesIO()
    buffer.write(html.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="bug_report.html",
        mimetype="text/html"
    )

@app.route("/export_pdf")
def export_pdf():
    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bugs")
    bugs = cursor.fetchall()
    conn.close()

    # 🔹 Статистика
    stats = {}
    for bug in bugs:
        key = f"{bug[6]} {bug[7]}"  # Severity + Priority
        stats[key] = stats.get(key, 0) + 1

    # 🔹 Генерируем HTML для PDF
    html = "<h2>Bug Report</h2>"
    html += "<h3>Statistics</h3><ul>"
    for key, count in stats.items():
        html += f"<li>{key}: {count}</li>"
    html += "</ul>"

    html += "<table border='1' cellspacing='0' cellpadding='5'>"
    html += "<tr><th>ID</th><th>Title</th><th>Severity</th><th>Priority</th><th>Description</th>"
    html += "<th>Steps</th><th>Expected</th><th>Actual</th></tr>"

    for bug in bugs:
        html += "<tr>"
        html += f"<td>{bug[0]}</td>"
        html += f"<td>{bug[1]}</td>"
        html += f"<td>{bug[6]}</td>"
        html += f"<td>{bug[7]}</td>"
        html += f"<td>{bug[2]}</td>"
        html += f"<td>{bug[3]}</td>"
        html += f"<td>{bug[4]}</td>"
        html += f"<td>{bug[5]}</td>"
        html += "</tr>"
    html += "</table>"

    # 🔹 Конвертация HTML в PDF
    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")  # путь к wkhtmltopdf
    pdf = pdfkit.from_string(html, False, configuration=config)

    # 🔹 Возвращаем PDF как скачиваемый файл
    buffer = BytesIO(pdf)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="bug_report.pdf",
        mimetype="application/pdf"
    )

# 🔹 Старт сервера
if __name__ == "__main__":
    app.run(debug=True)

    print("Registered routes:", app.url_map)