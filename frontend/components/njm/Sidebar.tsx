"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Building2, ShieldCheck, Briefcase, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string | null;
  icon: React.ElementType;
  active: boolean;
  accentVar: string | null;
  disabled: boolean;
}

export default function Sidebar() {
  const pathname = usePathname();

  // Extract brand ID if currently on a brand route
  const brandMatch = pathname.match(/^\/brand\/([^/]+)/);
  const brandId = brandMatch ? brandMatch[1] : null;

  const navItems: NavItem[] = [
    {
      label: "Agency Hub",
      href: "/",
      icon: Building2,
      active: pathname === "/",
      accentVar: "--agency-accent",
      disabled: false,
    },
    {
      label: "CEO Workspace",
      href: brandId ? `/brand/${brandId}/ceo` : null,
      icon: ShieldCheck,
      active: !!brandId && pathname.includes("/ceo"),
      accentVar: "--ceo-accent",
      disabled: !brandId,
    },
    {
      label: "PM Workspace",
      href: brandId ? `/brand/${brandId}/pm` : null,
      icon: Briefcase,
      active: !!brandId && pathname.includes("/pm"),
      accentVar: "--pm-accent",
      disabled: !brandId,
    },
    {
      label: "Configuración",
      href: "/settings",
      icon: Settings,
      active: pathname === "/settings",
      accentVar: null,
      disabled: false,
    },
  ];

  return (
    <aside className="fixed left-0 top-0 h-screen w-[240px] flex flex-col z-40 border-r border-white/[0.06] glass-subtle">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/[0.06]">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center font-black text-slate-950 text-sm shrink-0"
          style={{ background: "hsl(var(--pm-accent))" }}
        >
          N
        </div>
        <div className="min-w-0">
          <p className="font-bold text-foreground text-sm leading-tight">NJM OS</p>
          <p className="text-[10px] text-muted-foreground truncate">Agentic Workspace</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;

          if (item.disabled) {
            return (
              <div
                key={item.label}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-muted-foreground/30 cursor-not-allowed select-none"
                title="Selecciona una marca primero"
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="text-sm font-medium">{item.label}</span>
              </div>
            );
          }

          return (
            <Link
              key={item.label}
              href={item.href!}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-150",
                item.active
                  ? "bg-white/[0.08] text-foreground"
                  : "text-muted-foreground hover:bg-white/[0.05] hover:text-foreground"
              )}
            >
              <Icon
                className="w-4 h-4 shrink-0"
                style={
                  item.active && item.accentVar
                    ? { color: `hsl(var(${item.accentVar}))` }
                    : undefined
                }
              />
              <span className="text-sm font-medium flex-1">{item.label}</span>
              {item.active && (
                <span
                  className="w-1.5 h-1.5 rounded-full shrink-0"
                  style={{
                    background: item.accentVar
                      ? `hsl(var(${item.accentVar}))`
                      : "hsl(var(--muted-foreground))",
                  }}
                />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-white/[0.06]">
        <p className="text-[10px] text-muted-foreground/40 font-mono">v0.1.0 · NJM OS</p>
      </div>
    </aside>
  );
}
