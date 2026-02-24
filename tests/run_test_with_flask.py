# run_test_with_flask.py
import subprocess
import time
import requests
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

PROJECT_DIR = "D:/Python_Dela/BuRGA/burga-tracker"
TEST_RESULT_PATH = os.path.join("D:/Python_Dela/BuRGA/burga-tracker/tests", "test_bugmaker.txt")
FLASK_APP = "app.py"

# Запускаем Flask (скрипт app.py) в отдельном процессе
flask_process = subprocess.Popen([
    sys.executable,
    FLASK_APP,
], cwd=PROJECT_DIR)

try:
    # Ждём, пока сервер доступен
    print("Ждём, пока Flask сервер станет доступен...")
    server_up = False
    for _ in range(20):  # максимум 20 попыток
        try:
            r = requests.get("http://127.0.0.1:5000")
            if r.status_code == 200:
                server_up = True
                break
        except requests.RequestException:
            pass
        time.sleep(1)

    if not server_up:
        raise Exception("Flask сервер не поднялся за 20 секунд")

    print("Сервер доступен! Запускаем автотест...")

    # Настраиваем Selenium
    browser = webdriver.Chrome()
    browser.get("http://127.0.0.1:5000")

    def trying_login(browser, title, description, steps, expected_result, actual_result, defenition):
        try:
            # Заполняем форму
            browser.find_element(By.NAME, "title").send_keys(title)
            browser.find_element(By.NAME, "description").send_keys(description)
            browser.find_element(By.NAME, "steps").send_keys(steps)
            browser.find_element(By.NAME, "expected_result").send_keys(expected_result)
            browser.find_element(By.NAME, "actual_result").send_keys(actual_result)

            # Нажимаем Submit
            browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(2)

            # Переходим на Dashboard
            browser.find_element(By.LINK_TEXT, "Go to Dashboard").click()
            time.sleep(2)

            # Проверка, что баг появился
            elements = browser.find_elements(By.XPATH, f"//td[text()='{title}']")
            if elements:
                print("Баг сохранен ✅")
            else:
                print("Баг не сохранен ❌")
                result = "Баг не сохранен"
                # Запись в файл
                with open(TEST_RESULT_PATH, "a", encoding="utf-8") as f:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{current_time} — {defenition} — {result}\n")
                return result

            # Удаление только что созданного бага
            row = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.XPATH, f"//tr[td[text()='{title}']]"))
            )
            delete_button = row.find_element(By.CLASS_NAME, "button-delete")
            delete_button.click()

            # Работа с alert
            WebDriverWait(browser, 2).until(EC.alert_is_present())
            alert = browser.switch_to.alert
            alert.accept()

            # Ждём, пока строка исчезнет
            WebDriverWait(browser, 5).until(EC.staleness_of(row))
            print("Баг удалён ✅")
            result = "Баг создан и удалён успешно"

        except Exception as e:
            print(f"Ошибка автотеста: {e}")
            result = f"Ошибка: {e}"

        # Запись в файл
        with open(TEST_RESULT_PATH, "a", encoding="utf-8") as f:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{current_time} — {defenition} — {result}\n")
        return result

    # Запуск теста
    test_data = [
        ("test@test.com", "test description", "test steps", "expected", "actual", "Полный тест")
    ]

    for title, description, steps, expected_result, actual_result, defenition in test_data:
        print(f"Тестируем: {title}")
        trying_login(browser, title, description, steps, expected_result, actual_result, defenition)

    time.sleep(3)
    browser.quit()

finally:
    # Завершаем Flask
    print("Останавливаем Flask сервер...")
    try:
        flask_process.terminate()
        flask_process.wait(timeout=5)
    except Exception:
        pass
    print("Сервер остановлен.")

    # Открываем файл отчёта, если он есть
    if os.path.exists(TEST_RESULT_PATH):
        try:
            os.startfile(TEST_RESULT_PATH)
        except Exception:
            pass

# Для запуска используйте команду в терминале:
#  python tests\run_test_with_flask.py