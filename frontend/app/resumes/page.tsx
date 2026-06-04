"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpDown, RefreshCw, Search, Trash2 } from "lucide-react";
import { ResumeVersionSummary, deleteResumeVersion, listResumeVersions } from "@/lib/api";

type ResumeFilters = { search: string; roleType: string; company: string; direction: "asc" | "desc" };
const initialFilters: ResumeFilters = { search: "", roleType: "", company: "", direction: "desc" };

export default function ResumeVersionsPage() {
  const [versions, setVersions] = useState<ResumeVersionSummary[]>([]);
  const [filters, setFilters] = useState(initialFilters);
  const [query, setQuery] = useState(initialFilters);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadVersions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setVersions(await listResumeVersions(query));
    } catch {
      setError("Failed to load resume versions.");
    } finally {
      setIsLoading(false);
    }
  }, [query]);

  useEffect(() => void loadVersions(), [loadVersions]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setQuery(filters);
  }

  async function remove(version: ResumeVersionSummary) {
    if (!window.confirm(`Delete ${version.name}?`)) return;
    try {
      await deleteResumeVersion(version.id);
      await loadVersions();
    } catch {
      setError("Failed to delete resume version.");
    }
  }

  return (
    <div className="space-y-5">
      <div><h1 className="text-3xl font-bold text-ink">Resume Versions</h1><p className="mt-2 text-sm text-ink/60">Review immutable base and tailored resume snapshots.</p></div>
      <form onSubmit={submit} className="grid gap-3 border-y border-ink/10 py-4 md:grid-cols-6">
        <label className="md:col-span-2"><span className="text-xs font-semibold text-ink/60">Search</span><div className="relative mt-1"><Search aria-hidden="true" className="absolute left-3 top-2.5 h-4 w-4 text-ink/35" /><input value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} className="w-full rounded-md border border-ink/15 py-2 pl-9 pr-3 text-sm" placeholder="Name, company, or role" /></div></label>
        <Filter label="Role Type" value={filters.roleType} onChange={(value) => setFilters({ ...filters, roleType: value })} />
        <Filter label="Company" value={filters.company} onChange={(value) => setFilters({ ...filters, company: value })} />
        <button type="submit" className="self-end rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">Search</button>
        <button type="button" onClick={() => setFilters({ ...filters, direction: filters.direction === "desc" ? "asc" : "desc" })} className="flex self-end items-center justify-center gap-2 rounded-md border border-ink/15 px-3 py-2 text-sm text-ink/70"><ArrowUpDown aria-hidden="true" className="h-4 w-4" /> {filters.direction.toUpperCase()}</button>
      </form>
      {error ? <ErrorState message={error} onRetry={loadVersions} /> : null}
      {isLoading ? <p className="text-sm text-ink/60">Loading resume versions...</p> : null}
      {!isLoading && !error && !versions.length ? <p className="border-y border-ink/10 py-8 text-sm text-ink/55">No resume versions yet.</p> : null}
      {!isLoading && versions.length ? <div className="overflow-x-auto rounded-md border border-ink/10 bg-white"><table className="w-full min-w-[880px] text-left text-sm"><thead className="bg-mist/70 text-xs uppercase text-ink/50"><tr><Header>Name</Header><Header>Role Type</Header><Header>Company</Header><Header>Job Title</Header><Header>Version</Header><Header>Created At</Header><Header>Source</Header><Header>Action</Header></tr></thead><tbody>{versions.map((version) => <tr key={version.id} className="border-t border-ink/10"><Cell><Link href={`/resumes/${version.id}`} className="font-semibold text-leaf">{version.name}</Link></Cell><Cell>{version.role_type ?? "-"}</Cell><Cell>{version.company ?? "-"}</Cell><Cell>{version.job_title ?? "-"}</Cell><Cell>v{version.version_number}</Cell><Cell>{new Date(version.created_at).toLocaleDateString()}</Cell><Cell>{version.created_from}</Cell><Cell>{version.is_base ? <span className="text-xs font-semibold text-ink/45">Protected</span> : <button type="button" onClick={() => void remove(version)} className="text-coral" title="Delete resume version"><Trash2 aria-hidden="true" className="h-4 w-4" /></button>}</Cell></tr>)}</tbody></table></div> : null}
    </div>
  );
}

function Filter({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label><span className="text-xs font-semibold text-ink/60">{label}</span><input value={value} onChange={(event) => onChange(event.target.value)} className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 text-sm" /></label>; }
function Header({ children }: { children: React.ReactNode }) { return <th className="px-4 py-3 font-semibold">{children}</th>; }
function Cell({ children }: { children: React.ReactNode }) { return <td className="px-4 py-3 text-ink/70">{children}</td>; }
function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) { return <div className="flex items-center justify-between rounded-md border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral"><span>{message}</span><button type="button" onClick={onRetry} className="flex items-center gap-1 font-semibold"><RefreshCw aria-hidden="true" className="h-4 w-4" /> Retry</button></div>; }
