# Modelagem do MaintFlow

Documentação baseada no esquema SQLite definido em `app.py`. Os nomes físicos das tabelas são `users`, `equipment`, `orders` e `history`.

## Modelo conceitual e lógico

Um equipamento pode ter várias ordens de serviço. Cada ordem pertence a um equipamento e pode ter vários registros de histórico. Cada registro de histórico identifica o usuário responsável pela ação.

```text
Equipamento (1) ───── (0..N) Ordem de Serviço
Ordem de Serviço (1) ───── (0..N) Histórico
Usuário (1) ───── (0..N) Histórico
```

O banco permite uma ordem sem registros de histórico; o fluxo da aplicação insere o registro de abertura junto com a criação da ordem. O usuário não está vinculado diretamente à ordem: sua autoria é registrada no histórico.

## Dicionário de dados e modelo físico

| Tabela | Campo | Tipo SQLite | Regra e significado |
|---|---|---|---|
| users | id | INTEGER | Chave primária; identificador do usuário |
| users | username | TEXT | Obrigatório e único; nome usado no login |
| users | password | TEXT | Obrigatório; hash da senha, não a senha em texto |
| equipment | id | INTEGER | Chave primária; identificador do equipamento |
| equipment | tag | TEXT | Obrigatório e único; identificação normalizada em maiúsculas pela aplicação |
| equipment | name | TEXT | Obrigatório; nome do equipamento |
| equipment | sector | TEXT | Obrigatório; setor |
| equipment | description | TEXT | Não nulo; descrição opcional com valor padrão vazio |
| orders | id | INTEGER | Chave primária; número da ordem |
| orders | equipment_id | INTEGER | Obrigatório; chave estrangeira para equipment.id |
| orders | description | TEXT | Obrigatório; descrição do serviço |
| orders | priority | TEXT | Obrigatório; Baixa, Média ou Alta, validado pela aplicação |
| orders | status | TEXT | Obrigatório; padrão Aberta; transições validadas pela aplicação |
| orders | created_at | TEXT | Obrigatório; CURRENT_TIMESTAMP na criação, em UTC |
| orders | updated_at | TEXT | Obrigatório; data de criação ou última mudança de status, em UTC |
| history | id | INTEGER | Chave primária; identificador do evento |
| history | order_id | INTEGER | Obrigatório; chave estrangeira para orders.id |
| history | user_id | INTEGER | Obrigatório; chave estrangeira para users.id |
| history | action | TEXT | Obrigatório; descrição da abertura ou mudança de status |
| history | created_at | TEXT | Obrigatório; CURRENT_TIMESTAMP do evento, em UTC |

## Regras implementadas no código

- Login necessário para equipamentos, ordens, histórico e painel.
- Cadastro do primeiro usuário disponível apenas enquanto a tabela users estiver vazia.
- Senhas armazenadas com hash; formulários protegidos por token CSRF.
- Limites de equipamento: tag 40, nome 120, setor 120 e descrição 2000 caracteres.
- Descrição de ordem: de 1 a 2000 caracteres.
- Status: Aberta → Em andamento → Concluída; não há reabertura nesta versão.
- Chaves estrangeiras habilitadas em cada conexão com PRAGMA foreign_keys = ON.
- Prioridade e status são controlados pela aplicação, sem restrições CHECK no banco.
- Não há edição ou exclusão de equipamentos, múltiplos perfis ou anexos nesta versão.

## Organização da aplicação

```text
Navegador
    │ formulários e páginas
    ▼
Flask — rotas, sessão, validações e consultas parametrizadas
    ├── templates — HTML com Jinja
    ├── static — CSS
    └── SQLite — usuários, equipamentos, ordens e histórico
```

Essa documentação descreve a implementação. Resultados de avaliações por colegas devem ser registrados com base nos testes reais, separadamente da modelagem.
