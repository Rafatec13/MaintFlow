import tempfile
import unittest
from pathlib import Path
from app import app, init_db, db


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        app.config.update(TESTING=True, DATABASE=str(Path(self.temp.name) / 'test.db'))
        init_db()
        self.client = app.test_client()
        self.client.get('/configurar')

    def tearDown(self):
        self.temp.cleanup()

    def post(self, path, data):
        with self.client.session_transaction() as session:
            data = dict(data, csrf=session['csrf'])
        return self.client.post(path, data=data, follow_redirects=True)

    def authenticate(self):
        self.post('/configurar', {'username': 'rafael', 'password': 'teste-local-123'})
        return self.post('/login', {'username': 'rafael', 'password': 'teste-local-123'})

    def test_full_maintenance_workflow_and_persistence(self):
        self.assertEqual(self.authenticate().status_code, 200)
        self.post('/equipamentos', {'tag': 'bomba-01', 'name': 'Bomba', 'sector': 'Produção'})
        self.post('/ordens', {'equipment_id': '1', 'description': 'Verificar ruído', 'priority': 'Alta'})
        self.post('/ordens/1/status', {'status': 'Em andamento'})
        self.post('/ordens/1/status', {'status': 'Concluída'})
        with app.app_context():
            self.assertEqual(db().execute('SELECT status FROM orders').fetchone()[0], 'Concluída')
            self.assertEqual(db().execute('SELECT COUNT(*) FROM history').fetchone()[0], 3)
        self.assertIn('Concluída', self.client.get('/equipamentos/1/historico').get_data(as_text=True))
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_access_credentials_csrf_and_logout(self):
        self.assertEqual(self.client.get('/equipamentos').status_code, 302)
        self.assertEqual(self.client.post('/configurar', data={}).status_code, 400)
        self.authenticate()
        self.post('/sair', {})
        result = self.post('/login', {'username': 'rafael', 'password': 'incorreta'})
        self.assertIn('incorretos', result.get_data(as_text=True))
        self.assertEqual(self.client.get('/ordens').status_code, 302)

    def test_invalid_records_duplicates_and_status(self):
        self.authenticate()
        data = {'tag': 'eq-01', 'name': 'Motor', 'sector': 'Oficina'}
        self.post('/equipamentos', data)
        self.assertIn('Já existe', self.post('/equipamentos', data).get_data(as_text=True))
        self.post('/ordens', {'equipment_id': '999', 'description': 'Serviço', 'priority': 'Alta'})
        with app.app_context():
            self.assertEqual(db().execute('SELECT COUNT(*) FROM orders').fetchone()[0], 0)
        self.post('/ordens', {'equipment_id': '1', 'description': '<script>alert(1)</script>', 'priority': 'Média'})
        self.assertIn('&lt;script&gt;', self.client.get('/ordens').get_data(as_text=True))
        self.post('/ordens/1/status', {'status': 'Concluída'})
        with app.app_context():
            self.assertEqual(db().execute('SELECT status FROM orders').fetchone()[0], 'Aberta')
        self.assertEqual(self.client.get('/equipamentos/999/historico').status_code, 404)


if __name__ == '__main__':
    unittest.main()
