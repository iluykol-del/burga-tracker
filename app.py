from flask import Flask, render_template, request, redirect, send_file, Response
import sqlite3
import os
import matplotlib.pyplot as plt
import base64
import sqlite3
from io import BytesIO
from werkzeug.utils import secure_filename

# 🔹 Создаём объект Flask
app = Flask(__name__)

# 🔹 Для проверки, что запускается правильный файл
print("RUNNING FILE:", os.path.abspath(__file__))

# 🔹 Подключение к SQLite и проверка структуры таблицы
def init_db():
    conn = sqlite3.connect("bugs.db") # подключаемся к БД, если её нет
    cursor = conn.cursor()
    # Создаем таблицу, если её нет
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            steps TEXT,
            expected TEXT,
            actual TEXT,
            severity TEXT,
            priority TEXT,
            attachment BLOB
        )
    """)
    conn.commit()
    conn.close()
    print("Database initialized with attachment column")

# 🔹 В начале app.py вызываем инициализацию базы
init_db()

# Главная страница — форма создания бага
@app.route("/")
def home():
    return render_template("form.html") # form.html — это шаблон с формой для создания бага

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

    # Обработка attachment
    attachment_file = request.files.get('attachment')
    attachment_data = None
    if attachment_file and attachment_file.filename != "":
        attachment_data = attachment_file.read()

    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bugs 
        (title, description, steps, expected, actual, severity, priority, attachment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, description, steps, expected_result, actual_result, severity, priority, attachment_data))

    conn.commit()
    conn.close()
    return redirect("/") # после сохраннеия бага возврат на главную страницу 

# Дашборд со списком багов
@app.route("/dashboard")
def dashboard():
    # Получаем параметры фильтрации и сортировки из URL
    severity_filter = request.args.get("severity", "All")
    priority_filter = request.args.get("priority", "All")
    sort_by = request.args.get("sort_by", "id")
    sort_order = request.args.get("sort_order", "asc")  # asc-возрастание или desc-убывание 

    # Подключаемся к БД и формируем запрос с учетом фильтров и сортировки
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

    # Сортировка
    if sort_by in ["id", "title", "severity", "priority"]:
        query += f" ORDER BY {sort_by} {sort_order.upper()}"

    cursor.execute(query, params)
    bugs = cursor.fetchall()
    conn.close()

    # Для кнопки toggle: меняем порядок на противоположный
    next_order = "desc" if sort_order == "asc" else "asc"

    # Рендерим шаблон с данными
    return render_template(
        "dashboard.html",
        bugs=bugs,
        severity_filter=severity_filter,
        priority_filter=priority_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        next_order=next_order
    )
# вывод вложений
@app.route("/attachment/<int:bug_id>")
def attachment(bug_id):
    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT attachment FROM bugs WHERE id = ?", (bug_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return Response(row[0], mimetype="image/png")
    return "", 404

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
    if request.method == "POST":
        # Получаем данные из формы редактирования
        title = request.form["title"]
        description = request.form["description"]
        steps = request.form["steps"]
        expected = request.form["expected"]
        actual = request.form["actual"]
        severity = request.form["severity"]
        priority = request.form["priority"]
        
        attachment_file = request.files.get('attachment')
        attachment_data = None
        if attachment_file and attachment_file.filename != "":
            attachment_data = attachment_file.read()

        conn = sqlite3.connect("bugs.db")
        cursor = conn.cursor()
        if attachment_data:
            cursor.execute("""
                UPDATE bugs
                SET title=?, description=?, steps=?, expected=?, actual=?, severity=?, priority=?, attachment=?
                WHERE id=?
            """, (title, description, steps, expected, actual, severity, priority, attachment_data, bug_id))
        else:
            cursor.execute("""
                UPDATE bugs
                SET title=?, description=?, steps=?, expected=?, actual=?, severity=?, priority=?
                WHERE id=?
            """, (title, description, steps, expected, actual, severity, priority, bug_id))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    # GET-запрос — показываем форму с текущими данными
    conn = sqlite3.connect("bugs.db")
    cursor = conn.cursor()
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

    # 🔹 Статистика по Severity
    severity_counts = {"Critical": 0, "Major": 0, "Minor": 0}
    for bug in bugs:
        sev = bug[6]  # bug[6] = Severity
        if sev in severity_counts:
            severity_counts[sev] += 1

    # 🔹 Генерация круговой диаграммы
    labels = []
    sizes = []
    colors = []

    for sev, count in severity_counts.items():
        if count > 0:
            labels.append(sev)
            sizes.append(count)
            if sev == "Critical":
                colors.append("red")
            elif sev == "Major":
                colors.append("orange")
            else:
                colors.append("green")

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=90, colors=colors)
    ax.axis("equal")  # Круглая форма

    # 🔹 Сохраняем в base64 для вставки в HTML
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    # 🔹 Формируем HTML
    html = """<!DOCTYPE html>
    <html lang="ru">
    <head>
    <meta charset="UTF-8">
    <title>Bug Report</title>
    </head>
    <body>
    """

    html += "<h3>Severity Distribution</h3>"
    html += f'<img src="data:image/png;base64,{img_base64}" alt="Severity Chart">'

    html += "<h3>Statistics</h3><ul>"
    for sev, count in severity_counts.items():
        html += f"<li>{sev}: {count}</li>"
    html += "</ul>"

    html += "<table border='1'>"
    html += "<tr><th>ID</th><th>Title</th><th>Severity</th><th>Priority</th>"
    html += "<th>Description</th><th>Steps</th><th>Expected</th><th>Actual</th><th>Attachment</th></tr>"

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
        if bug[8]:
            img_b64 = base64.b64encode(bug[8]).decode("utf-8")
            html += f"<td><img src='data:image/png;base64,{img_b64}' width='100'></td>"
        else:
            html += "<td>No attachment</td>"
        html += "</tr>"
    html += "</table>"
    html += "</body></html>"

    # 🔹 Возвращаем HTML для скачивания
    buffer = BytesIO()
    buffer.write(html.encode("utf-8"))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="bug_report.html",
        mimetype="text/html"
    )
# 🔹 Старт сервера
if __name__ == "__main__":
    print("Registered routes:", app.url_map)
    app.run(debug=True)