import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Media Compose Dashboard",
  description: "Dashboard de monitoramento para ilhas de edição",
};

/**
 * Script injetado no <head> e executado ANTES da hidratação do React.
 * Objetivo: aplicar a classe "dark"/color-scheme já no primeiro paint,
 * lendo a preferência salva (localStorage) ou, na ausência dela, a
 * preferência do sistema operacional — isso evita o "flash" de tema
 * claro seguido de troca para escuro (FOUC de tema).
 *
 * A mesma chave (media-compose-theme) e a mesma lógica de toggle são
 * usadas depois em components/Header.tsx, quando o usuário troca o
 * tema manualmente.
 */
const themeInitializerScript = `
  (function () {
    try {
      var storedTheme = localStorage.getItem("media-compose-theme");
      var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      var shouldUseDark = storedTheme ? storedTheme === "dark" : prefersDark;
      var root = document.documentElement;
      root.classList.toggle("dark", shouldUseDark);
      root.style.colorScheme = shouldUseDark ? "dark" : "light";
    } catch (error) {
      document.documentElement.classList.remove("dark");
      document.documentElement.style.colorScheme = "light";
    }
  })();
`;

/** Layout raiz do App Router: envolve toda página do dashboard. */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // suppressHydrationWarning é necessário porque o script acima altera
    // a classe do <html> antes do React hidratar, o que normalmente
    // geraria um warning de mismatch client/server.
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitializerScript }} />
      </head>
      <body className="
          bg-slate-50 text-slate-900
          dark:bg-slate-950 dark:text-[rgba(227,227,233,1)]
          transition-colors duration-300
        "
      >{children}
      </body>
    </html>
  );
}
