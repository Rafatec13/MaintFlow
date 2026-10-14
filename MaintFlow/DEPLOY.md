# Hospedagem no PythonAnywhere

O mesmo código Flask pode ser executado localmente ou hospedado no PythonAnywhere. O SQLite permanece em arquivo no diretório `instance` da instalação.

## Preparação

Envie os arquivos do projeto para `~/MaintFlow` e execute no console Bash:

```bash
cd ~/MaintFlow
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

## Configuração Web

Crie uma aplicação com configuração manual e Python 3.13. Para a conta usada no projeto:

- Código-fonte e diretório de trabalho: `/home/RafaelDamascenoTech/MaintFlow`
- Virtualenv: `/home/RafaelDamascenoTech/MaintFlow/.venv`

Substitua o conteúdo do arquivo WSGI por:

```python
import sys

project_path = '/home/RafaelDamascenoTech/MaintFlow'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from app import app as application
```

Salve e recarregue a aplicação na aba Web. Não execute `app.py` no console para publicar: o serviço Web importa a aplicação pelo WSGI.

## Primeiro acesso

Acesse `/configurar`, crie o usuário inicial e confira o login antes de compartilhar o endereço. A configuração inicial fica indisponível depois que o primeiro usuário é criado.

Confira cadastro de equipamento, abertura de ordem, avanço de status, histórico e painel no site publicado. Os três testes automatizados não substituem essa conferência nem os testes com cinco avaliadores exigidos no PIT II.

No plano gratuito, mantenha a validade do site pela aba Web. Faça backup do diretório `instance` antes de atualizar a aplicação. Esse diretório não deve ser enviado ao repositório.
