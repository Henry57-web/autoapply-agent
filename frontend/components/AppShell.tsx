"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, BriefcaseBusiness, Files, Mail, Settings, Sparkles } from "lucide-react";

const links = [
  { href: "/", label: "Dashboard", icon: BarChart3 },
  { href: "/jobs", label: "Jobs", icon: BriefcaseBusiness },
  { href: "/resumes", label: "Resumes", icon: Files },
  { href: "/emails", label: "Emails", icon: Mail },
  { href: "/generate", label: "Tailor Resume", icon: Sparkles },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <main className="min-h-screen bg-[#f6f7f3]">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-5 py-7 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-ink/10 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-coral">AI Job Application Platform</p>
            <Link href="/" className="mt-1 block text-2xl font-bold text-ink">AutoApply Agent</Link>
          </div>
          <nav className="flex flex-wrap gap-1 rounded-md border border-ink/10 bg-white p-1 shadow-sm">
            {links.map(({ href, label, icon: Icon }) => {
              const active = href === "/" ? pathname === href : pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-2 rounded px-3 py-2 text-sm font-semibold transition ${
                    active ? "bg-ink text-white" : "text-ink/60 hover:text-ink"
                  }`}
                >
                  <Icon aria-hidden="true" className="h-4 w-4" />
                  {label}
                </Link>
              );
            })}
          </nav>
        </header>
        {children}
      </div>
    </main>
  );
}
