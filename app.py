from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB_FILE = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            assignee TEXT,
            priority TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Новая',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks ORDER BY CASE priority WHEN "Высокий" THEN 1 WHEN "Средний" THEN 2 ELSE 3 END, due_date').fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/create', methods=['GET', 'POST'])
def create_task():
    if request.method == 'POST':
        title = request.form['title'].strip()
        if not title:
            return render_template('create.html', error="Название задачи обязательно")
        description = request.form['description'].strip()
        assignee = request.form['assignee'].strip()
        priority = request.form['priority']
        due_date = request.form['due_date']

        if due_date:
            try:
                datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                return render_template('create.html', error="Неверный формат даты")

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO tasks (title, description, assignee, priority, due_date) VALUES (?, ?, ?, ?, ?)',
            (title, description, assignee, priority, due_date)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
def task_detail(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
    conn.close()
    if not task:
        return "Задача не найдена", 404
    
    if task['due_date']:
        due = datetime.strptime(task['due_date'], '%Y-%m-%d')
        days_left = (due - datetime.now()).days
        is_overdue = days_left < 0 and task['status'] != 'Готово'
    else:
        days_left = None
        is_overdue = False
        
    return render_template('detail.html', task=task, days_left=days_left, is_overdue=is_overdue)

@app.route('/task/<int:task_id>/status', methods=['POST'])
def update_status(task_id):
    status = request.form['status']
    if status not in ['Новая', 'В работе', 'Готово', 'Отложено']:
        return "Неверный статус", 400
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET status=? WHERE id=?', (status, task_id))
    conn.commit()
    conn.close()
    return redirect(url_for('task_detail', task_id=task_id))

@app.route('/task/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/reports')
def reports():
    conn = get_db_connection()
    tasks_rows = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()

    tasks = [dict(row) for row in tasks_rows]

    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == 'Готово'])
    overdue = len([t for t in tasks if t['due_date'] and datetime.strptime(t['due_date'], '%Y-%m-%d') < datetime.now() and t['status'] != 'Готово'])
    
    status_counts = {}
    priority_counts = {}
    assignees = sorted({t['assignee'] for t in tasks if t.get('assignee')})
    statuses = sorted({t['status'] for t in tasks if t.get('status')})
    for t in tasks:
        status_counts[t['status']] = status_counts.get(t['status'], 0) + 1
        priority_counts[t['priority']] = priority_counts.get(t['priority'], 0) + 1

    return render_template('reports.html', 
                           tasks=tasks, 
                           total=total, 
                           completed=completed, 
                           overdue=overdue,
                           status_counts=status_counts,
                           priority_counts=priority_counts,
                           assignees=assignees,
                           statuses=statuses)
def seed_demo_data():
    conn = get_db_connection()
    if conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0] == 0:
        vr_project_tasks = [
            ('Изучение актуальных тем для разработки проекта в виртуальной реальности', 'Изучение современных тенденций и технологий в VR разработке', 'Георгий', 'Высокий', '2025-09-10', 'Готово'),
            ('Выбор и формулирование темы проекта в виртуальной реальности', 'Определение конкретной темы и направленности VR проекта', 'Артём', 'Средний', '2025-09-15', 'Готово'),
            ('Составление плана выполнения проекта с ключевыми дедлайнами', 'Создание детального плана разработки с этапами и сроками', 'Василий', 'Высокий', '2025-09-20', 'Готово'),
            ('Формулировка цели и задач проекта', 'Определение основных целей и конкретных задач VR проекта', 'Георгий', 'Низкий', '2025-09-25', 'Готово'),
            ('Формирование списка используемых источников', 'Сбор и систематизация библиографических источников', 'Георгий', 'Низкий', '2025-09-25', 'Готово'),
            ('Разработка идеи проекта с реализацией механик в виртуальной реальности', 'Проектирование основных механик и геймплейных элементов', 'Артём', 'Высокий', '2025-10-01', 'Готово'),
            ('Продумывание и визуализация итогового результата', 'Создание концепт-артов и визуального представления проекта', 'Василий', 'Средний', '2025-10-10', 'Готово'),
            ('Разработка 3D-моделей для проекта', 'Создание трехмерных моделей объектов и окружения для VR', 'Василий', 'Высокий', '2025-11-20', 'В работе'),
            ('Разработка механик, программирование', 'Программирование основных игровых механик и взаимодействий', 'Георгий', 'Высокий', '2025-11-20', 'В работе'),
            ('Сборка проекта', 'Интеграция всех компонентов в единый VR проект', 'Артём', 'Высокий', '2025-11-20', 'В работе'),
            ('Тестирование работы механик со шлемом виртуальной реальности', 'Проверка функциональности и удобства использования в VR', 'Георгий', 'Средний', '2025-11-25', 'Новая'),
            ('Тестирование работы механик со шлемом виртуальной реальности', 'Проверка функциональности и удобства использования в VR', 'Артём', 'Средний', '2025-11-25', 'Новая'),
            ('Написание текста проекта', 'Подготовка документации и описания проекта', 'Василий', 'Низкий', '2025-12-01', 'Новая'),
            ('Запись видео с демонстрацией механик', 'Создание демонстрационного ролика работы VR приложения', 'Артём', 'Высокий', '2025-12-10', 'Новая'),
            ('Подготовка презентации проекта', 'Разработка презентационных материалов для защиты', 'Георгий', 'Средний', '2025-12-10', 'Новая'),
            ('Защита проекта', 'Презентация и защита готового VR проекта', 'Георгий', 'Высокий', '2025-12-15', 'Новая'),
            ('Защита проекта', 'Презентация и защита готового VR проекта', 'Артём', 'Высокий', '2025-12-15', 'Новая'),
            ('Защита проекта', 'Презентация и защита готового VR проекта', 'Василий', 'Высокий', '2025-12-15', 'Новая')
        ]
        
        conn.executemany(
            'INSERT INTO tasks (title, description, assignee, priority, due_date, status) VALUES (?, ?, ?, ?, ?, ?)',
            vr_project_tasks
        )
        conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_demo_data()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
