"use client";

import { Ilha } from "@/types/dashboard";

type Props = {
  ilhas: Ilha[];

  search: string;
  onSearch: (v: string) => void;

  editorFilter: string;
  onEditorFilter: (v: string) => void;

  statusFilter: string;
  onStatusFilter: (v: string) => void;

  retrancaFilter: string;
  onRetrancaFilter: (v: string) => void;
};

/**
 * Barra de filtros acima do grid de ilhas: busca por texto, retranca,
 * editor e status. As opções de cada select são derivadas da própria
 * lista de ilhas recebida (não vêm de uma rota separada), então elas
 * já refletem só o que existe naquele momento.
 */
export default function FilterBar({
  ilhas,
  search,
  onSearch,
  editorFilter,
  onEditorFilter,
  statusFilter,
  onStatusFilter,
  retrancaFilter,
  onRetrancaFilter,
}: Props) {

  const editors = Array.from(
    new Set(ilhas.map((i) => i.editor).filter(Boolean))
  );

  // Exibe: PROGRAMA - RETRANCA
  // Duplicado em app/page.tsx (ilhasFiltradas usa a mesma composição para
  // comparar com este valor selecionado).
  const retrancas = Array.from(
    new Set(
      ilhas.map((i) => {
        if (i.programa && i.retranca) {
          return `${i.programa} - ${i.retranca}`;
        }

        return i.projeto;
      })
    )
  );

  return (
    <div className="flex flex-wrap gap-3">

      <input
        type="text"
        placeholder="Buscar projeto..."
        value={search}
        onChange={(e) => onSearch(e.target.value)}
        className="flex-1 min-w-[220px] rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-sm text-white placeholder-slate-500 outline-none focus:border-cyan-500/50"
      />

      <select
        value={retrancaFilter}
        onChange={(e) => onRetrancaFilter(e.target.value)}
        className="rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-sm text-white outline-none focus:border-cyan-500/50"
      >
        <option value="">
          Todas as retrancas
        </option>

        {retrancas.map((retranca) => (
          <option key={retranca} value={retranca}>
            {retranca}
          </option>
        ))}
      </select>

      <select
        value={editorFilter}
        onChange={(e) => onEditorFilter(e.target.value)}
        className="rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-sm text-white outline-none focus:border-cyan-500/50"
      >
        <option value="">
          Todos os editores
        </option>

        {editors.map((e) => (
          <option key={e} value={e}>
            {e}
          </option>
        ))}
      </select>

      <select
        value={statusFilter}
        onChange={(e) => onStatusFilter(e.target.value)}
        className="rounded-lg border border-white/10 bg-slate-900 px-4 py-2 text-sm text-white outline-none focus:border-cyan-500/50"
      >
        <option value="">
          Todos os status
        </option>

        <option value="Ocupado">
          Ocupado
        </option>

        <option value="Concluido">
          Concluido
        </option>
      </select>

    </div>
  );
}
