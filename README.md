🐞 Bug Tracker (Flask + SQLite)

Простой веб-трекер багов на Flask с возможностью:
добавлять баги
фильтровать и сортировать их
прикреплять изображения (скриншоты)
просматривать изображения в модальном окне
экспортировать отчёт в HTML (с таблицей и диаграммой)
редактировать и удалять баги
Проект предназначен для учебных целей и небольших локальных проектов.

🚀 Возможности

✅ Добавление багов с полями:

Title
Description
Steps
Expected result
Actual result
Severity (Critical / Major / Minor)
Priority (High / Medium / Low)
Attachment (изображение)

✅ Dashboard:

сортировка по ID, Title, Severity, Priority
фильтрация по Severity и Priority
просмотр изображений в popup (modal window)
кнопки Edit / Delete

✅ Экспорт в HTML:

таблица всех багов
встроенные изображения (base64)
диаграмма распределения Severity
статистика по количеству багов

🛠️ Стек технологий

Python 3.x
Flask
SQLite
HTML + CSS
JavaScript (modal popup)
Matplotlib (диаграмма)

📂 Структура проекта
burga-tracker/
│
├── app.py
├── bugs.db
├── templates/
│   ├── home.html
│   ├── dashboard.html
│   ├── edit.html
│
├── static/
│   ├── style.css
│
└── README.md

⚙️ Установка и запуск
1️⃣ Клонировать проект
git clone <repo_url>
cd burga-tracker
2️⃣ Установить зависимости
pip install flask matplotlib
3️⃣ Запустить сервер
python app.py
4️⃣ Открыть в браузере
http://127.0.0.1:5000
🗄️ База данных

Используется SQLite (bugs.db).

Таблица bugs:

Поле	Тип
id	INTEGER
title	TEXT
description	TEXT
steps	TEXT
expected	TEXT
actual	TEXT
severity	TEXT
priority	TEXT
attachment	BLOB

Изображения сохраняются прямо в БД в формате BLOB.

🖼️ Работа с изображениями

изображения сохраняются в БД
отображаются в таблице как миниатюры
по клику открываются в модальном окне
при экспорте в HTML встраиваются как base64

📤 Экспорт отчёта

Кнопка Export HTML генерирует файл:
bug_report.html

В файле:
диаграмма Severity Distribution
статистика по багам
таблица со всеми багами
изображения вложены внутрь HTML

🧩 Основные маршруты
Route	Описание
/форма добавления бага
/submit	сохранение бага
/dashboard	список багов
/edit/<id>	редактирование
/delete/<id>	удаление
/attachment/<id>	получение изображения
/export	экспорт HTML
/clear	очистка БД

🎨 UI особенности

таблица с сортировкой
фильтры по Severity и Priority
modal popup для просмотра картинки
кастомный CSS

⚠️ Ограничения

проект не предназначен для production
используется Flask dev server
нет авторизации
нет ограничений размера файла
нет защиты от XSS/SQL injection (учебный проект)

📌 Планы по улучшению (TODO)

улучшение дизайна
тёмная тема


👨‍💻 Автор

Проект создан в учебных целях как pet-project для изучения:
Flask
SQLite
HTML/CSS
работы с изображениями
генерации HTML-отчётов