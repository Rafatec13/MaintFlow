# MaintFlow

Aplicação de gestão de manutenção para execução local no Windows, desenvolvida em Python, Flask, HTML, CSS e SQLite.

Endereço configurado para hospedagem: https://rafaeldamascenotech.pythonanywhere.com/

O acesso público após a configuração WSGI ainda precisa ser conferido no navegador. Instruções de publicação: [DEPLOY.md](DEPLOY.md).

## Executar no Windows

1. Instale Python 3.11 ou superior, com o lançador `py` habilitado.
2. Extraia a pasta do projeto e execute `iniciar.bat`. A primeira execução precisa de internet para baixar as dependências.
3. Abra http://127.0.0.1:5000 no navegador.
4. Crie o usuário e a senha na configuração inicial. Não existe senha padrão.
5. Mantenha o terminal aberto enquanto usa a aplicação. Pressione Ctrl+C para encerrar.

Alternativa pelo terminal, dentro da pasta do projeto:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

## Fluxo de uso

Cadastre um equipamento com tag, nome e setor. Abra uma ordem vinculada a ele, informe a descrição e escolha a prioridade. Use **Iniciar** e **Concluir** para avançar os status. Consulte o histórico pelo cadastro de equipamentos e os totais no painel.

O histórico registra a abertura e as mudanças de status, com usuário e data em UTC. A aplicação possui um usuário inicial e não inclui múltiplos perfis, anexos, edição/exclusão de equipamentos ou recuperação de senha nesta versão.

## Dados e organização

- `app.py`: rotas, validações, autenticação e acesso ao banco.
- `templates/`: páginas HTML com Jinja.
- `static/style.css`: estilos e adaptação a telas menores.
- `instance/maintflow.db`: banco SQLite, criado automaticamente.
- `instance/secret.key`: chave de sessão gerada na primeira execução.

Faça backup da pasta `instance` com o servidor encerrado. Não publique essa pasta no Git. O servidor escuta somente no endereço local `127.0.0.1`, porta 5000.

As senhas são armazenadas com hash; os formulários usam proteção CSRF e as consultas ao banco são parametrizadas. O modo de depuração está desativado.

## Verificação

Execute `py -3 -m unittest discover -s tests -v` no ambiente com as dependências instaladas. Os testes usam banco temporário e não alteram os dados da instalação.

Em 13/10/2026, os três testes automatizados foram executados no PythonAnywhere com Python 3.13.1 e concluíram com `OK`, conforme captura do console. Eles verificam autenticação, CSRF, encerramento de sessão, fluxo de manutenção, persistência, registros inválidos, duplicidades e transições de status. A inspeção da aplicação publicada pelo navegador permanece pendente.

A avaliação pelos cinco colegas, suas evidências, o laudo acadêmico e o vídeo continuam pendentes. Os testes automatizados não substituem essas atividades.
