/**
 * Tipos compartilhados do Media Compose Dashboard.
 *
 * Este arquivo é o contrato entre o frontend e a API do backend
 * (backend/routes/dashboard_routes.py, rota GET /dashboard). Sempre que
 * um campo mudar de nome/formato no backend, ele deve mudar aqui também
 * — é o único lugar de tipagem do payload no frontend inteiro.
 */

/** Indicadores agregados exibidos nos cards do topo do dashboard. */
export type Summary = {
  totalIlhas: number;
  ilhasAtivas: number;
  tempoMedioMin: number;
  concluidosHoje: number;
};

/**
 * Uma ilha de edição (estação de trabalho do Avid Media Composer)
 * monitorada pelo agente de coleta (agent/monitor.py).
 */
export type Ilha = {
  id: number;

  editor?: string;
  avatar?: string;

  ilha: string;

  // Vocabulário real emitido pelo backend (routes/dashboard_routes.py),
  // que apenas capitaliza o status vindo do agente ("ocupado" | "concluido").
  status: "Ocupado" | "Concluido";

  projeto: string;

  // Programa e retranca são extraídos do nome da pasta monitorada pelo
  // agente (ex: "ANIVERSARIO RECIFE LUC I9") e sempre vêm preenchidos pelo
  // backend, ainda que vazios (routes/dashboard_routes.py usa
  // ed.get("programa", "") / ed.get("retranca", "")).
  programa: string;
  retranca: string;

  progresso: number;

  inicio: string;

  arquivoGb: number;

  // Campos previstos pelo serviço de IA (data_ia/predictor.py), repassados
  // pelo backend junto com o restante dos dados da ilha.
  previsaoRestanteMin: number;

  previsaoFim: string;

  editorTexto?: string;

  reporter?: string;

  carga?: number;

  regional?: string;
};

/** Um item da fila de entregas prevista, mostrado no AIPanel. */
export type FilaEntrega = {
  id: number;
  editor: string;
  projeto: string;
  horario: string;
  restanteMin: number;
};

/** Bloco de dados vindos do serviço de predição (data_ia). */
export type IAData = {
  fila: FilaEntrega[];
  precisaoModelo: number;
  dadosTreinamento: number;
};

/** Um ponto de dado genérico usado pelos gráficos (Recharts). */
export type ChartPoint = {
  label: string;
  valor: number;
};

/** Formato completo da resposta de GET /dashboard. */
export type DashboardData = {
  atualizadoEm: string;
  statusSistema: string;
  summary: Summary;
  ilhas: Ilha[];
  ia: IAData;
  horasPorDia: ChartPoint[];
  atividadePorHora: ChartPoint[];
};

/**
 * Perfil de visualização do dashboard. Hoje app/page.tsx fixa "gerente"
 * (comentário "futuramente virá do login/backend"); o componente
 * ViewModeSelector já existe pronto para quando essa alternância for
 * ligada à autenticação real.
 */
export type ViewMode = "gerente" | "gestor" | "publico";
