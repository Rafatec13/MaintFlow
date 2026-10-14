import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE = Path(__file__).resolve().parent
DATA = BASE / 'instance'
DATA.mkdir(exist_ok=True)
key_file = DATA / 'secret.key'
if not key_file.exists():
    key_file.write_text(secrets.token_hex(32), encoding='utf-8')
app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get('MAINTFLOW_SECRET', key_file.read_text().strip()),
                  DATABASE=str(DATA / 'maintflow.db'), SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Lax', MAX_CONTENT_LENGTH=1024 * 1024)


def db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    connection = g.pop('db', None)
    if connection:
        connection.close()


def init_db():
    with app.app_context():
        db().executescript('''
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS equipment (
          id INTEGER PRIMARY KEY, tag TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
          sector TEXT NOT NULL, description TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS orders (
          id INTEGER PRIMARY KEY, equipment_id INTEGER NOT NULL REFERENCES equipment(id),
          description TEXT NOT NULL, priority TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'Aberta', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS history (
          id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id),
          user_id INTEGER NOT NULL REFERENCES users(id), action TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        ''')
        db().commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


@app.before_request
def protect_forms():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_hex(32)
    if request.method == 'POST':
        if not secrets.compare_digest(session['csrf'], request.form.get('csrf', '')):
            return 'Formulário expirado. Atualize a página e tente novamente.', 400


@app.context_processor
def template_context():
    return {'csrf': session.get('csrf', '')}


@app.route('/configurar', methods=['GET', 'POST'])
def setup():
    if db().execute('SELECT id FROM users LIMIT 1').fetchone():
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not 3 <= len(username) <= 60 or not 8 <= len(password) <= 200:
            flash('Use um usuário de 3 a 60 caracteres e uma senha de 8 a 200 caracteres.', 'error')
        else:
            db().execute('INSERT INTO users(username,password) VALUES (?,?)',
                         (username, generate_password_hash(password)))
            db().commit()
            flash('Usuário criado. Entre para continuar.', 'success')
            return redirect(url_for('login'))
    return render_template('auth.html', setup=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not db().execute('SELECT id FROM users LIMIT 1').fetchone():
        return redirect(url_for('setup'))
    if request.method == 'POST':
        user = db().execute('SELECT * FROM users WHERE username=?',
                            (request.form.get('username', '').strip(),)).fetchone()
        if user and check_password_hash(user['password'], request.form.get('password', '')):
            session.clear()
            session.update(user_id=user['id'], username=user['username'], csrf=secrets.token_hex(32))
            return redirect(url_for('dashboard'))
        flash('Usuário ou senha incorretos.', 'error')
    return render_template('auth.html', setup=False)


@app.post('/sair')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.get('/')
@login_required
def dashboard():
    total = db().execute('SELECT COUNT(*) FROM equipment').fetchone()[0]
    counts = {status: 0 for status in ['Aberta', 'Em andamento', 'Concluída']}
    for row in db().execute('SELECT status, COUNT(*) AS total FROM orders GROUP BY status'):
        counts[row['status']] = row['total']
    recent = db().execute('SELECT o.*, e.name, e.tag FROM orders o JOIN equipment e ON e.id=o.equipment_id ORDER BY o.id DESC LIMIT 5').fetchall()
    return render_template('dashboard.html', total=total, counts=counts, orders=recent)


@app.route('/equipamentos', methods=['GET', 'POST'])
@login_required
def equipment():
    if request.method == 'POST':
        values = [request.form.get(k, '').strip() for k in ['tag', 'name', 'sector', 'description']]
        values[0] = values[0].upper()
        if not all(values[:3]) or any(len(v) > limit for v, limit in zip(values, [40, 120, 120, 2000])):
            flash('Preencha tag, nome e setor dentro dos limites indicados.', 'error')
        else:
            try:
                db().execute('INSERT INTO equipment(tag,name,sector,description) VALUES (?,?,?,?)', values)
                db().commit()
                flash('Equipamento cadastrado.', 'success')
                return redirect(url_for('equipment'))
            except sqlite3.IntegrityError:
                db().rollback()
                flash('Já existe um equipamento com essa tag.', 'error')
    items = db().execute('SELECT * FROM equipment ORDER BY name').fetchall()
    return render_template('equipment.html', items=items)


@app.get('/equipamentos/<int:equipment_id>/historico')
@login_required
def equipment_history(equipment_id):
    item = db().execute('SELECT * FROM equipment WHERE id=?', (equipment_id,)).fetchone()
    if not item:
        return 'Equipamento não encontrado.', 404
    orders = db().execute('SELECT * FROM orders WHERE equipment_id=? ORDER BY id DESC', (equipment_id,)).fetchall()
    events = db().execute('''SELECT h.*, u.username, o.id AS number FROM history h
      JOIN users u ON u.id=h.user_id JOIN orders o ON o.id=h.order_id
      WHERE o.equipment_id=? ORDER BY h.id DESC''', (equipment_id,)).fetchall()
    return render_template('history.html', item=item, orders=orders, events=events)


@app.route('/ordens', methods=['GET', 'POST'])
@login_required
def orders():
    if request.method == 'POST':
        equipment_id = request.form.get('equipment_id', '')
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', '')
        valid_equipment = db().execute('SELECT id FROM equipment WHERE id=?', (equipment_id,)).fetchone()
        if not valid_equipment or not 1 <= len(description) <= 2000 or priority not in ['Baixa', 'Média', 'Alta']:
            flash('Selecione um equipamento, descreva o serviço e escolha uma prioridade válida.', 'error')
        else:
            cursor = db().execute('INSERT INTO orders(equipment_id,description,priority) VALUES (?,?,?)',
                                  (equipment_id, description, priority))
            db().execute('INSERT INTO history(order_id,user_id,action) VALUES (?,?,?)',
                         (cursor.lastrowid, session['user_id'], 'Ordem aberta'))
            db().commit()
            flash('Ordem de serviço aberta.', 'success')
            return redirect(url_for('orders'))
    items = db().execute('SELECT * FROM equipment ORDER BY name').fetchall()
    status = request.args.get('status', '')
    query = 'SELECT o.*, e.name, e.tag FROM orders o JOIN equipment e ON e.id=o.equipment_id'
    params = ()
    if status in ['Aberta', 'Em andamento', 'Concluída']:
        query += ' WHERE o.status=?'
        params = (status,)
    records = db().execute(query + ' ORDER BY o.id DESC', params).fetchall()
    return render_template('orders.html', items=items, orders=records, selected=status)


@app.post('/ordens/<int:order_id>/status')
@login_required
def update_status(order_id):
    order = db().execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
    if not order:
        return 'Ordem não encontrada.', 404
    next_status = {'Aberta': 'Em andamento', 'Em andamento': 'Concluída'}.get(order['status'])
    if request.form.get('status') != next_status or not next_status:
        flash('Alteração de status inválida.', 'error')
    else:
        cursor = db().execute('UPDATE orders SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND status=?',
                             (next_status, order_id, order['status']))
        if cursor.rowcount:
            db().execute('INSERT INTO history(order_id,user_id,action) VALUES (?,?,?)',
                         (order_id, session['user_id'], 'Status alterado para ' + next_status))
            flash('Status atualizado.', 'success')
        else:
            flash('Esta ordem já foi alterada. Confira o status atual.', 'error')
        db().commit()
    return redirect(url_for('orders'))


init_db()
if __name__ == '__main__':
    from waitress import serve
    print('MaintFlow disponível em http://127.0.0.1:5000')
    serve(app, host='127.0.0.1', port=5000)
