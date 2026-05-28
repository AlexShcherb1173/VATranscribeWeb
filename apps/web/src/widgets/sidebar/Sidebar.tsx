import { NavLink } from "react-router-dom";

import { useI18n } from "@/shared/i18n";

const navItems = [
  { to: "/app", key: "dashboard", icon: "⌘" },
  { to: "/app/downloads", key: "downloads", icon: "↧" },
  { to: "/app/files", key: "files", icon: "□" },
  { to: "/app/jobs", key: "jobs", icon: "●" },
  { to: "/app/transcriptions", key: "transcripts", icon: "¶" },
  { to: "/app/billing", key: "billing", icon: "$" },
  { to: "/app/profile", key: "profile", icon: "◐" },
  { to: "/app/settings", key: "settings", icon: "⚙" },
] as const;

export function Sidebar() {
  const { t } = useI18n();

  return (
    <aside className="sticky top-0 hidden h-screen border-r border-slate-200/80 bg-white/70 p-5 backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/80 lg:block">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white shadow-lg dark:bg-cyan-300 dark:text-slate-950">
          VA
        </div>
        <div>
          <div className="font-semibold tracking-tight text-slate-950 dark:text-white">VATranscribe</div>
          <div className="text-xs text-slate-500 dark:text-slate-400">{t.common.creatorOs}</div>
        </div>
      </div>

      <nav className="space-y-1.5">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/app"}
            className={({ isActive }) =>
              [
                "flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition",
                isActive
                  ? "bg-slate-950 text-white shadow-lg shadow-slate-950/10 dark:bg-white dark:text-slate-950"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-white",
              ].join(" ")
            }
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-slate-100 text-xs dark:bg-white/10">
              {item.icon}
            </span>
            <span>{t.nav[item.key]}</span>
          </NavLink>
        ))}
      </nav>

    </aside>
  );
}
