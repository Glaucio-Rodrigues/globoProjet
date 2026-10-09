import { ViewMode } from "@/types/dashboard";

type Props = {
  viewMode: ViewMode;
  onChange: (mode: ViewMode) => void;
};

const options: { label: string; value: ViewMode; description: string }[] = [
  {
    label: "Gerente",
    value: "gerente",
    description: "Visão global completa",
  },
  {
    label: "Gestor",
    value: "gestor",
    description: "Visão por time/projeto",
  },
  {
    label: "Público / TV",
    value: "publico",
    description: "Visão sem dados sensíveis",
  },
];

/**
 * Seletor de perfil de acesso (gerente/gestor/público).
 *
 * NOTA: ainda não é renderizado em app/page.tsx — o viewMode ali está
 * fixo em "gerente" com o comentário "futuramente virá do login/backend".
 * Este componente já está pronto para quando essa integração existir;
 * basta importar e passar viewMode/onChange vindos do estado de auth.
 */
export default function ViewModeSelector({ viewMode, onChange }: Props) {
  return (
    <section className="rounded-2xl border border-white/10 bg-slate-950 p-4">
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-white">Controle de acesso</h2>
        <p className="text-xs text-slate-400">
          Selecione a visão do dashboard conforme o perfil do usuário.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {options.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`rounded-xl border p-4 text-left transition ${
              viewMode === option.value
                ? "border-cyan-400 bg-cyan-400/10"
                : "border-white/10 bg-slate-900 hover:bg-slate-800"
            }`}
          >
            <p
              className={`text-sm font-semibold ${
                viewMode === option.value ? "text-cyan-300" : "text-white"
              }`}
            >
              {option.label}
            </p>

            <p className="mt-1 text-xs text-slate-400">
              {option.description}
            </p>
          </button>
        ))}
      </div>
    </section>
  );
}
