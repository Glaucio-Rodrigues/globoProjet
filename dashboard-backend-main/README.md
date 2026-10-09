# Media Compose Dashboard — Monitoramento e Inteligência para Ilhas de Edição

Ecossistema para transformar a atividade bruta das ilhas de edição em dados estratégicos e previsões em tempo real. Ele resolve o desafio de gestores que precisam saber quem está operando, em qual projeto e, principalmente, quando o trabalho será concluído — sem interromper o fluxo criativo dos editores.

![Diagrama](./img/diagram.png)

## Como o Sistema Funciona

O sistema opera de forma silenciosa e automática, seguindo quatro grandes etapas que conectam a estação de trabalho do editor à tela do gestor.

### 1. Captura Invisível (a ponta)

Tudo começa na estação de trabalho onde o **Avid Media Composer** está rodando. O **Agente de Coleta** (`agent/monitor.py`) fica vigilante no plano de fundo usando um Watchdog de sistema de arquivos.

- **Ação**: sempre que o editor salva o projeto ou o Avid faz um backup automático, o Agente detecta a movimentação no armazenamento.
- **Diferencial**: o editor não aperta nenhum botão extra — o monitoramento é feito por meio dos eventos do próprio sistema operacional.

### 2. Processamento Instantâneo (o agora)

Assim que o Agente percebe uma mudança, envia um `POST /events` para o backend Flask.

- A informação de que o "Editor X" está trabalhando no "Projeto Y" é gravada em uma memória de alta velocidade (**Redis**), atualizada em milissegundos.
- O Dashboard consulta esse estado via `GET /dashboard` com polling a cada poucos segundos.

### 3. Memória Institucional (o passado)

Enquanto o Redis mostra o que está acontecendo agora, o **Worker ETL** (`backend/worker/worker.py`) consome a fila de eventos e persiste tudo no **PostgreSQL**: início da edição, fim da edição, tempo total de uso e o tamanho dos arquivos manipulados — eliminando planilhas manuais de produtividade.

### 4. Predição com Inteligência Artificial (o futuro)

O serviço `data_ia` (Scikit-Learn — Regressão Linear) analisa o histórico de edições encerradas por editor e, quando o backend recebe um evento em andamento, consulta esse modelo para estimar quantos minutos faltam e exibe no Dashboard: *"Previsão de término: 15h30"*. Enquanto não há histórico suficiente (mínimo de 10 edições concluídas por editor), o sistema não expõe uma previsão para aquela ilha.

---

## Arquitetura

```
Avid salva arquivo na pasta do projeto
           ↓
   agent/monitor.py          ← Watchdog: detecta mudanças no SO
           ↓  HTTP POST /events
   backend/Flask (app.py)    ← Recebe e distribui
           ↓  RPUSH                              ↘ POST /predict (best-effort)
   Redis (fila "eventos_watchdog")          data_ia/predictor.py  ← Scikit-Learn (ETC)
           ↓  BLPOP                                    ↑
   backend/worker/worker.py  ← ETL: transforma e persiste
           ↓
   PostgreSQL                ← Histórico completo + status dos projetos
```

| Camada | Tecnologia | Papel |
|---|---|---|
| **Coleta (Agente)** | Python + Watchdog | Monitoramento leve de eventos do SO (criação/edição), sem sobrecarga de storage. |
| **Backend (API)** | Flask | Recebe eventos do agente e serve o dashboard. |
| **Mensageria/Cache** | Redis | Estado transitório (ocupado/concluído) em memória, ~1ms de resposta. |
| **Banco de Dados** | PostgreSQL | Persistência de dados históricos para auditoria e treinamento de modelos. |
| **Inteligência (IA)** | Scikit-Learn / Pandas | Predição de tempo de conclusão (ETC) via regressão linear por editor. |
| **Processamento (ETL)** | Python (Worker) | Consome a fila Redis e grava usuários, projetos, eventos e edições no Postgres. |
| **Dashboard** | Next.js + Recharts | Interface reativa para acompanhamento gerencial (poll a cada 3s). |

---

## Convenção de Pastas

O sistema interpreta o **nome da pasta do projeto** para identificar editor, projeto e ilha automaticamente. O editor não precisa fazer nada além de trabalhar normalmente no Avid.

```
arquivos_teste/
└── ANIVERSARIO RECIFE LUC I9/     ← "ANIVERSARIO RECIFE" = projeto, "LUC" = código do editor, "I9" = ilha
    ├── video.avp                 ← qualquer arquivo aqui → projeto "ocupado"
    └── timeline/
        └── render.avb            ← arquivo dentro de /timeline/ → projeto marcado como "concluido"
```

- `<PROJETO> <CODIGO> <ILHA>`: os dois últimos tokens do nome da pasta são sempre o código do editor e a ilha (ex.: `I9` → `ILHA-09`); tudo antes disso é o nome do projeto.
- Conclusão é detectada pela presença de qualquer arquivo dentro da subpasta `timeline/` do projeto — reflete o padrão real de export do Avid Media Composer.

### Mapa de códigos de editor

A fonte única de verdade é `agent/usuario_map.py` (dicionário `USUARIO_MAP`). Para adicionar um editor novo:

1. Descubra o código usado na pasta (penúltimo token do nome, maiúsculo).
2. Adicione uma linha em `agent/usuario_map.py`: `"CODIGO": "Nome Completo"`.
3. Salve — `agent/monitor.py` já usa automaticamente via `resolver_usuario()`.

---

## Estrutura do Projeto

```
globo2-PE/
├── start.sh                    # Sobe todo o ecossistema de uma vez
├── stop.sh                     # Encerra tudo
├── docker-compose.yml          # Orquestração dos containers
├── docker.py                   # Helper para subir/derrubar o Compose
├── .env                        # Variáveis de ambiente (não versionar valores reais)
├── .env.example                # Referência de variáveis
│
├── agent/
│   ├── monitor.py              # Watchdog — monitora a pasta e envia eventos ao backend
│   ├── usuario_map.py          # Fonte única de verdade: código → nome do editor
│   ├── arquivos_teste/         # Pasta monitorada (simula o storage do Avid)
│   └── requirements.txt
│
├── backend/
│   ├── app.py                  # Flask — entry point da API
│   ├── database.py             # Conexões lazy com Redis e PostgreSQL
│   ├── routes/
│   │   ├── event_routes.py     # POST /events, GET /events/status, GET /events/fila
│   │   ├── dashboard_routes.py # GET /dashboard
│   │   └── health_routes.py    # GET /health
│   ├── worker/
│   │   └── worker.py           # ETL — consome fila Redis e persiste no Postgres
│   └── requirements.txt
│
├── data_ia/
│   ├── predictor.py            # API Flask (porta 5001) — treina e serve o modelo de ETC
│   └── requirements.txt
│
├── frontend/                    # Dashboard Next.js (consome GET /dashboard)
│
├── postgres/
│   └── init.sql                # Schema inicial (mesmas tabelas criadas pelo worker)
│
└── redis_config/
    └── redis.conf               # Configuração usada pelo container Redis
```

---

## Pré-requisitos

- Docker + Docker Compose
- Python 3.11+
- `python-venv` (para o agente local)

---

## Como Usar

### 1. Subir tudo com um comando

```bash
chmod +x start.sh stop.sh   # apenas na primeira vez
./start.sh
```

O script faz automaticamente:
1. Sobe os containers Docker (Postgres + Redis + Backend + IA)
2. Aguarda o backend estar respondendo em `:5000`
3. Inicia o Worker ETL dentro do container do backend
4. Cria o virtualenv do agente (só na primeira vez)
5. Inicia o Watchdog em foreground (logs visíveis no terminal)

### 2. Encerrar tudo

```bash
./stop.sh
```

---

## Simular Atividade (Testes)

```bash
# Criar pasta de projeto (edição em andamento)
mkdir -p agent/arquivos_teste/"ANIVERSARIO RECIFE LUC I9"
touch agent/arquivos_teste/"ANIVERSARIO RECIFE LUC I9"/video.avp

# Sinalizar conclusão do projeto (qualquer arquivo dentro de /timeline/)
mkdir -p agent/arquivos_teste/"ANIVERSARIO RECIFE LUC I9/timeline"
touch agent/arquivos_teste/"ANIVERSARIO RECIFE LUC I9/timeline"/render.avb
```

---

## Rotas da API

### Backend (`http://localhost:5000`)

#### `GET /health`
Verifica se o backend está no ar.

```json
{ "status": "ok", "message": "Backend funcionando corretamente" }
```

---

#### `POST /events`
Recebe eventos do Watchdog. Corpo esperado (é exatamente o que `agent/monitor.py` envia):

```json
{
  "tipoEvento": "modified",
  "arquivo":    "video.avp",
  "caminho":    "/abs/path/ANIVERSARIO RECIFE LUC I9/video.avp",
  "diretorio":  false,
  "timestamp":  "2026-08-04 17:27:00",
  "pasta":      "ANIVERSARIO RECIFE LUC I9",
  "ilha":       "ILHA-09",
  "usuario":    "Lucas Cardoso Alecrim",
  "projeto":    "ANIVERSARIO RECIFE",
  "status":     "ocupado",
  "tamanho_mb": 128.4
}
```

Resposta:
```json
{ "status": "ok", "message": "Evento enfileirado com sucesso", "fila": 1, "data": { ... } }
```

Internamente esse endpoint: enfileira o evento no Redis (`RPUSH eventos_watchdog`) para o Worker ETL persistir no Postgres, atualiza o estado em tempo real do editor (`HSET editor:<nome>`) e, se o evento ainda estiver em andamento, consulta o serviço de IA (`data_ia`) para anexar uma previsão de conclusão.

---

#### `GET /events/status`
Retorna o estado **em tempo real** de todos os editores (via Redis).

```json
{
  "total": 1,
  "editores": [
    {
      "status":      "ocupado",
      "editor":      "Lucas Cardoso Alecrim",
      "ilha":        "ILHA-09",
      "projeto":     "Aniversario Recife",
      "arquivo":     "video.avp",
      "ultimo_save": "2026-08-04 17:25:00",
      "tamanho_mb":  "128.4",
      "previsao_restante_min": "18",
      "previsao_fim": "17:43"
    }
  ]
}
```

---

#### `GET /events/fila`
Retorna quantos eventos estão pendentes na fila do Redis (sem consumir).

```json
{ "fila": "eventos_watchdog", "tamanho": 3 }
```

---

#### `GET /dashboard`
Retorna o estado atual do dashboard, montado a partir do Redis (tempo real). Métricas que dependem de agregações históricas (`tempoMedioMin`, `concluidosHoje`, gráficos, precisão do modelo) ainda não são calculadas a partir do Postgres e chegam zeradas/vazias — é o próximo passo natural de evolução do backend.

### IA (`http://localhost:5001`) — `data_ia/predictor.py`

#### `POST /predict`
```json
{ "editor": "Lucas Cardoso Alecrim", "tamanho_mb": 128.4 }
```
```json
{ "editor": "Lucas Cardoso Alecrim", "tamanho_mb": 128.4, "minutos": 18 }
```

#### `POST /retrain`
Força o retreinamento do modelo global com os dados mais recentes da tabela `edicoes`.

#### `GET /health`
Healthcheck do serviço de IA.

---

## Tabelas do PostgreSQL

Criadas automaticamente pelo Worker (`backend/worker/worker.py`) e também via `postgres/init.sql` na primeira subida do container.

### `usuarios`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | SERIAL | PK |
| `nome` | TEXT | Nome completo do editor |
| `criado_em` | TIMESTAMPTZ | Data de criação |

### `projetos`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | SERIAL | PK |
| `nome` | TEXT | Nome do projeto |
| `usuario_id` | INT | FK → usuarios |
| `status` | TEXT | `em_andamento` ou `concluido` |
| `concluido_em` | TIMESTAMPTZ | Preenchido quando entra um arquivo em `/timeline/` |
| `criado_em` | TIMESTAMPTZ | Data de criação |

### `eventos`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | SERIAL | PK |
| `tipo` | TEXT | `created`, `modified`, `deleted`, `moved` |
| `arquivo` | TEXT | Nome do arquivo |
| `caminho` | TEXT | Caminho absoluto |
| `pasta` | TEXT | Nome da pasta do projeto |
| `is_final` | BOOLEAN | `true` se o evento sinalizou conclusão (`status == "concluido"`) |
| `usuario_id` | INT | FK → usuarios |
| `projeto_id` | INT | FK → projetos |
| `ocorrido_em` | TIMESTAMPTZ | Timestamp do evento |

### `edicoes`
Usada pela camada de IA (`data_ia/predictor.py`) para calcular o ETC (Estimated Time of Completion).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | SERIAL | PK |
| `editor` | TEXT | Nome do editor |
| `arquivo` | TEXT | Arquivo sendo editado |
| `projeto` | TEXT | Nome do projeto |
| `inicio_edicao` | TIMESTAMPTZ | Primeiro evento detectado |
| `fim_edicao` | TIMESTAMPTZ | Preenchido quando o evento chega com `status == "concluido"` |
| `duracao_segundos` | INT | Calculado automaticamente |
| `tamanho_arquivo_mb` | FLOAT | Usado pelo modelo de IA como feature de treino |

---

## Inteligência Artificial: como funciona

A IA transforma o monitoramento passivo em análise preditiva. Em vez de apenas dizer o que está acontecendo agora, ela projeta o futuro.

1. **Fonte do conhecimento**: `data_ia/predictor.py` lê a tabela `edicoes` do PostgreSQL, filtrando apenas edições já encerradas (`fim_edicao` preenchido) com duração e tamanho de arquivo válidos.
2. **Modelo**: Regressão Linear (Scikit-Learn), treinado por editor sempre que possível (mínimo de 10 amostras); cai para um modelo global e, na ausência de dados, para uma estimativa linear simples (~1.8 min a cada 100MB).
3. **Inferência**: quando o backend recebe um evento em andamento com `tamanho_mb`, ele chama `POST /predict` no serviço de IA e anexa `previsao_restante_min` / `previsao_fim` ao estado do editor no Redis — consumido depois pelo `/dashboard`.
4. **Retreinamento**: cada edição concluída vira uma nova linha em `edicoes`, alimentando o próximo retreinamento (manual via `POST /retrain`, ou automático na primeira chamada após reiniciar o serviço).

Se o serviço `data_ia` estiver fora do ar ou sem dados suficientes, o backend simplesmente não anexa previsão ao evento — a ingestão de eventos nunca falha por causa da IA.

---

## Consultas Úteis

```bash
# Ver status atual de todos os projetos
docker exec globo2-postgres psql -U globo_user -d globo2_db -c "
SELECT p.nome AS projeto, u.nome AS usuario, p.status, p.concluido_em
FROM projetos p JOIN usuarios u ON u.id = p.usuario_id;"

# Ver últimos eventos registrados
docker exec globo2-postgres psql -U globo_user -d globo2_db -c "
SELECT u.nome AS usuario, p.nome AS projeto, e.tipo, e.arquivo, e.is_final, e.ocorrido_em
FROM eventos e
JOIN usuarios u ON u.id = e.usuario_id
JOIN projetos p ON p.id = e.projeto_id
ORDER BY e.ocorrido_em DESC LIMIT 20;"

# Ver fila Redis (eventos pendentes)
docker exec globo2-redis redis-cli LLEN eventos_watchdog

# Ver estado em tempo real dos editores
docker exec globo2-redis redis-cli KEYS "editor:*"
docker exec globo2-redis redis-cli HGETALL "editor:lucas_cardoso_alecrim"

# Logs do worker ETL
docker exec globo2-backend cat /tmp/worker.log

# Logs do backend Flask
docker logs globo2-backend

# Logs do serviço de IA
docker logs globo2-data-ia

# Testar previsão de ETC manualmente
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{"editor": "Lucas Cardoso Alecrim", "tamanho_mb": 500}'
```

---

## Variáveis de Ambiente

Definidas em `.env` (use `.env.example` como referência) e lidas automaticamente pelo `docker compose` no `docker-compose.yml`:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DB_HOST` | `postgres` | Host do PostgreSQL |
| `DB_PORT` | `5432` | Porta do PostgreSQL |
| `DB_NAME` | `globo2_db` | Nome do banco |
| `DB_USER` | `globo_user` | Usuário |
| `DB_PASSWORD` | `123456` | Senha (troque em produção) |
| `REDIS_HOST` | `redis` | Host do Redis |
| `REDIS_PORT` | `6379` | Porta do Redis |
| `PREDICTOR_URL` | `http://data_ia:5001` | URL do serviço de IA consultado pelo backend |

---

## Resumo de Responsabilidades

| Componente | Função Principal |
| :---- | :---- |
| **Watchdog (`agent/monitor.py`)** | Gatilho de eventos — detecta quando o Avid salva arquivos. |
| **Flask (`backend/app.py`)** | Recebe os eventos e serve o dashboard. |
| **Redis** | Estado momentâneo (agora). |
| **PostgreSQL** | Histórico e auditoria (passado). |
| **Scikit-Learn (`data_ia`)** | Inteligência e previsão (futuro). |
| **Next.js (`frontend`)** | Interface visual para o gestor. |

---

## Contribuindo com o Projeto

A partir de agora, todo commit segue as diretrizes de engenharia do projeto (detalhamento completo em `Globo2-PE_Diretrizes_Engenharia.pdf`).

### Padrão de commits semânticos

Formato: `tipo(escopo): descrição no imperativo`.

| Tipo | Uso |
|------|-----|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Mudança estrutural sem alterar comportamento (ver Tidy First abaixo) |
| `chore` | Manutenção que não afeta código de produção (deps, configs, scripts) |
| `docs` | Documentação apenas |
| `test` | Testes, sem tocar em código de produção |
| `style` | Formatação/lint, sem impacto em lógica |
| `perf` | Melhoria de performance mensurável |
| `build` | Processo de build/dependências |
| `ci` | Pipelines de integração contínua |
| `revert` | Reversão de um commit anterior |

O escopo é livre (o CI não valida contra uma lista fixa), mas siga essa convenção pra manter consistência: `backend`, `worker`, `agent`, `data`, `db`, `ia`, `data_ia`, `devops`, `docs`. Exemplo: `feat(data_ia): adiciona previsão por ilha além de por editor`.

**Regra de ouro:** um commit muda um tipo de coisa só. Nunca misture `refactor` com `feat` no mesmo commit.

### Refatoração com Tidy First

Baseado em *Tidy First?* (Kent Beck, O'Reilly): separe sempre mudanças **estruturais** (como o código está organizado) de mudanças de **comportamento** (o que o código faz). Antes de implementar uma feature em código confuso, faça pequenas arrumações (`refactor`) primeiro — guard clauses, remoção de dead code, extração de variáveis/constantes explicativas, extração de helpers — cada uma em commit próprio, sem alterar nenhum teste. Só depois vem o commit `feat`/`fix` com a mudança de comportamento em cima do código já limpo.

### Áreas de responsabilidade (referência)

| Área | Escopo no repositório | Escopo de commit sugerido |
|----------|------------------------|-------------------|
| Backend | `backend/` (API Flask + Worker ETL) | `backend`, `worker` |
| Dados | `postgres/` (schema e persistência) | `data`, `db` |
| IA | `data_ia/` (predição de ETC) | `ia`, `data_ia` |
| DevOps | `docker-compose.yml`, `start.sh`/`stop.sh`, `redis_config/`, CI/CD | `devops`, `ci`, `build` |
| Documentação | README, diagramas, guias | `docs` |

O `agent/` (Watchdog de coleta) é responsabilidade compartilhada de Backend + DevOps. Não há mais aprovação obrigatória por área (ver seção de branches abaixo) — essa tabela é só referência de quem mexe em quê.

### Fluxo de branches — commit direto na `staging`, depois promove pra `main`

```
seu commit (local)
      │  git push origin staging
      ▼
   staging   ← branch de integração, todo mundo commita/dá push aqui primeiro
      │  CI valida o padrão do commit (.github/workflows/ci.yml)
      │
      │  quando a staging estiver estável...
      ▼
    main     ← produção
```

Não existem mais branches por subgrupo nem aprovação obrigatória de líder via CODEOWNERS/branch protection — o GitHub Free não aplica essa trava em repositório privado de organização sem upgrade pago, então o fluxo depende da disciplina do time: **sempre trabalhar em cima da `staging`, nunca commitar direto na `main`.**

Passo a passo do dia a dia:

1. Atualize sua `staging` local:
   ```bash
   git checkout staging
   git pull origin staging
   ```
2. Faça as alterações e commite seguindo o padrão semântico acima.
3. Envie pra `staging`:
   ```bash
   git push origin staging
   ```
4. O GitHub Actions roda automaticamente e valida se a mensagem de cada commit está no formato certo. Se reprovar, corrija a mensagem (`git commit --amend` ou um novo commit de correção) e envie de novo.
5. Quando a `staging` estiver testada e estável, promova pra `main`:
   ```bash
   git checkout main
   git pull origin main
   git merge staging
   git push origin main
   ```
   Alternativa: abrir um Pull Request de `staging` para `main` pelo GitHub, se preferir revisar o diff antes de mergear (não é obrigatório — o CI também valida o título do PR nesse caso).

### Pipeline de CI

Todo `push`, em qualquer branch, roda `.github/workflows/ci.yml`: um `grep` simples que confere se cada commit novo segue o padrão `tipo(escopo): descrição`. Se alguém abrir um Pull Request por conta própria, o título do PR também é validado no mesmo padrão. Não há lint/build/QA obrigatórios no momento — só a validação de commit semântico.

### Esteira ágil

Sprints de 2 semanas + quadro Kanban contínuo: `Backlog → Refinamento → Em Desenvolvimento → Code Review → QA → Deploy → Concluído`. Toda issue recebe uma label de área já no refinamento; quem pega a tarefa trabalha localmente, commita seguindo o padrão semântico e envia pra `staging`.
