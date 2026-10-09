# Media Compose Dashboard — Frontend

Frontend do sistema de monitoramento de ilhas de edição: mostra em tempo real quem está
editando, em qual projeto, e a previsão de conclusão calculada pelo serviço de IA do
backend. Consome a API do `dashboard-backend` via polling a cada poucos segundos.

## Tecnologias

- Next.js 14 (App Router)
- React 18 + TypeScript
- Tailwind CSS
- Recharts (gráficos)

## Pré-requisitos

- Node.js 18.17 ou superior (recomendado 20 LTS)
- npm (vem junto com o Node)
- O `dashboard-backend` rodando localmente em `http://127.0.0.1:5000` — a URL da API
  está fixa em `app/page.tsx`, não há variável de ambiente pra isso ainda. Sem o
  backend no ar, o dashboard carrega mas fica sem dados.

## Como rodar o projeto

```bash
npm install       # instala as dependências (só precisa rodar de novo se o package.json mudar)
npm run dev        # sobe o servidor de desenvolvimento em http://localhost:3000
```

Outros comandos úteis:

```bash
npm run build      # build de produção (também roda a checagem de tipos do TypeScript)
npm run start       # serve o build de produção gerado por `npm run build`
npm run lint        # ESLint
```

## Estrutura do projeto

```
app/          Páginas e layout do App Router (Next.js)
components/   Componentes visuais do dashboard (cards, gráficos, filtros, etc.)
types/        Tipos TypeScript compartilhados (Summary, Ilha, DashboardData, etc.)
public/       Ícones e assets estáticos
docs/         Documentação complementar do projeto
```

## Contribuindo com o Projeto

A partir de agora, todo commit segue as diretrizes de engenharia do projeto (detalhamento
completo em `Globo2-PE_Diretrizes_Engenharia.pdf`, no repositório `dashboard-backend`).

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

O escopo é livre (o CI não valida contra uma lista fixa), mas siga essa convenção pra
manter consistência: `frontend`, `ui`, `design`, `docs`. Exemplo: `fix(frontend): corrige
polling do dashboard quando o backend está fora do ar`.

**Regra de ouro:** um commit muda um tipo de coisa só. Nunca misture `refactor` com
`feat` no mesmo commit.

### Refatoração com Tidy First

Baseado em *Tidy First?* (Kent Beck, O'Reilly): separe sempre mudanças **estruturais**
(como o código está organizado) de mudanças de **comportamento** (o que o código faz).
Antes de implementar uma feature em código confuso, faça pequenas arrumações
(`refactor`) primeiro — extração de constantes/variáveis explicativas, remoção de
duplicação, extração de componentes/helpers — cada uma em commit próprio. Só depois vem
o commit `feat`/`fix` com a mudança de comportamento em cima do código já limpo.

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

Não há branch por área nem aprovação obrigatória de líder via CODEOWNERS/branch
protection — o GitHub Free não aplica essa trava em repositório privado de organização
sem upgrade pago, então o fluxo depende da disciplina do time: **sempre trabalhar em
cima da `staging`, nunca commitar direto na `main`.**

Passo a passo do dia a dia:

1. Atualize sua `staging` local:
   ```bash
   git checkout staging
   git pull origin staging
   ```
2. Faça as alterações, teste com `npm run dev` / `npm run build`, e commite seguindo o
   padrão semântico acima.
3. Envie pra `staging`:
   ```bash
   git push origin staging
   ```
4. O GitHub Actions roda automaticamente e valida se a mensagem de cada commit está no
   formato certo. Se reprovar, corrija a mensagem (`git commit --amend` ou um novo
   commit de correção) e envie de novo.
5. Quando a `staging` estiver testada e estável, promova pra `main`:
   ```bash
   git checkout main
   git pull origin main
   git merge staging
   git push origin main
   ```
   Alternativa: abrir um Pull Request de `staging` para `main` pelo GitHub, se preferir
   revisar o diff antes de mergear (não é obrigatório — o CI também valida o título do
   PR nesse caso).

### Pipeline de CI

Todo `push`, em qualquer branch, roda `.github/workflows/ci.yml`: um `grep` simples que
confere se cada commit novo segue o padrão `tipo(escopo): descrição`. Se alguém abrir um
Pull Request por conta própria, o título do PR também é validado no mesmo padrão. Não há
lint/build obrigatórios no CI no momento — rode `npm run lint` e `npm run build`
localmente antes de enviar pra `staging`.
