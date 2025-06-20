import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'task_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Integer, nullable=False, default=50)  # 1-100, 默认50
    due_date = db.Column(db.Date)
    completed = db.Column(db.Boolean, default=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        priority = request.form.get('priority', 50)
        priority = int(priority) if priority else 50
        if not (1 <= priority <= 100):
            flash('优先级必须在1-100之间', 'error')
            return redirect(url_for('index'))
        due_date = request.form.get('due_date')
        due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
        task = Task(title=title, description=description, priority=priority, due_date=due_date)
        db.session.add(task)
        db.session.commit()
        flash('任务已添加', 'success')
        return redirect(url_for('index'))
    tasks = Task.query.order_by(Task.completed, Task.priority, Task.due_date).all()
    return render_template('index.html', tasks=tasks)

@app.route('/complete/<int:task_id>')
def complete(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('任务已删除', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form.get('description', '')
        priority = request.form.get('priority', 50)
        priority = int(priority) if priority else 50
        if not (1 <= priority <= 100):
            flash('优先级必须在1-100之间', 'error')
            return render_template('edit.html', task=task)
        task.priority = priority
        due_date = request.form.get('due_date')
        task.due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
        db.session.commit()
        flash('任务已更新', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', task=task)

@app.route('/update_field', methods=['POST'])
def update_field():
    data = request.get_json()
    task_id = data.get('task_id')
    field = data.get('field')
    value = data.get('value')
    task = Task.query.get(task_id)
    if not task or field not in {'title', 'description', 'priority', 'due_date'}:
        return jsonify({'success': False, 'msg': '无效请求'})
    try:
        if field == 'priority':
            if value == '' or value is None:
                value = 50  # 默认值
            else:
                value = int(value)
                if not (1 <= value <= 100):
                    return jsonify({'success': False, 'msg': '优先级必须为1-100'})
        if field == 'due_date':
            if value:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            else:
                value = None
        setattr(task, field, value)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'msg': str(e)})

# 兼容本地开发和生产环境的数据库初始化
if not os.path.exists('tasks.db'):
    with app.app_context():
        db.create_all()

# if __name__ == '__main__':
#     # 获取 Railway 提供的端口
#     port = int(os.environ.get('PORT', 5000))
#     # 重要：绑定到 0.0.0.0，不是 127.0.0.1
#     app.run(host='0.0.0.0', port=port, debug=True)
