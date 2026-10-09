📌 O QUE CONTÉM NESTE ARQUIVO:

 - HISTÓRICO: o que foi planejado quando o frontend ainda usava dados mockados.
 - STATUS ATUAL: o que já está de fato integrado com o backend.
 ---------------------------------------------------------------------------------------------
                                STATUS ATUAL (atualizado)

🟢 Integração com o backend: CONCLUÍDA

O frontend não usa mais dados mockados (`data/mockData.ts` foi removido). `app/page.tsx` busca
os dados reais em `GET http://127.0.0.1:5000/dashboard`, com:

- tela de carregamento na primeira busca
- tratamento de erro com botão "Tentar novamente"
- polling automático a cada 3 segundos (sem tela de loading nas atualizações silenciosas)

O que ainda depende de evolução do backend (não é um problema do frontend):
- `summary.tempoMedioMin` e `summary.concluidosHoje` — o backend ainda retorna 0 (requerem
  agregação sobre o PostgreSQL, que hoje só é usado pelo Worker/IA, não pelo endpoint /dashboard).
- `horasPorDia` e `atividadePorHora` — o backend ainda retorna listas vazias.
- `ia.precisaoModelo` e `ia.dadosTreinamento` — o backend ainda retorna 0.
- `previsaoRestanteMin` / `previsaoFim` por ilha já vêm do serviço de IA (`data_ia`) quando há
  histórico suficiente para aquele editor; caso contrário ficam em 0 / "--:--".

---------------------------------------------------------------------------------------------
                                HISTÓRICO (planejamento original)

🧱 Estrutura do projeto
Projeto criado com Next.js + TypeScript
Estilização com Tailwind CSS
Organização por pastas:
app/ → páginas
components/ → componentes reutilizáveis
types/ → tipagens

🎨 Interface implementada

O dashboard já possui:

Header (status + botão atualizar)
Cards de resumo (ilhas, tempo, etc.)
Navegação por abas
Lista de ilhas em atividade
Painel de Inteligência Artificial
Gráficos (Recharts)

🟣 Próximas melhorias (quando o backend expuser os dados)

🔗 tempoMedioMin / concluidosHoje via agregação no Postgres
📊 horasPorDia / atividadePorHora via agregação no Postgres
🧠 precisaoModelo / dadosTreinamento via data_ia
🔍 mais filtros e busca
