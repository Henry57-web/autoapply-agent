"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpDown, RefreshCw, Search } from "lucide-react";
import { JOB_STATUSES, JobStatus, JobSummary, listJobs } from "@/lib/api";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [filters, setFilters] = useState({ search: "", status: "" as JobStatus | "", minScore: "", maxScore: "", sortBy: "created_at" as "match_score" | "created_at" | "deadline", direction: "desc" as "asc" | "desc" });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadJobs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setJobs(await listJobs(filters));
    } catch {
      setError("Failed to load jobs.");
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  useEffect(() => void loadJobs(), [loadJobs]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadJobs();
  }

  return (
    <div className="space-y-6">
      <section><h1 className="text-3xl font-bold text-ink">Jobs</h1><p className="mt-2 text-sm text-ink/60">Search, sort, and manage your application pipeline.</p></section>
      <form onSubmit={handleSearch} className="grid gap-3 rounded-md border border-ink/10 bg-white p-4 shadow-sm md:grid-cols-6">
        <label className="md:col-span-2"><span className="text-xs font-semibold text-ink/60">Search</span><div className="relative mt-1"><Search aria-hidden="true" className="absolute left-3 top-2.5 h-4 w-4 text-ink/35" /><input value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} className="w-full rounded-md border border-ink/15 py-2 pl-9 pr-3 text-sm" placeholder="Company or position" /></div></label>
        <FilterSelect label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value as JobStatus | "" })}><option value="">All statuses</option>{JOB_STATUSES.map((status) => <option key={status}>{status}</option>)}</FilterSelect>
        <FilterInput label="Min Score" value={filters.minScore} onChange={(value) => setFilters({ ...filters, minScore: value })} />
        <FilterInput label="Max Score" value={filters.maxScore} onChange={(value) => setFilters({ ...filters, maxScore: value })} />
        <FilterSelect label="Sort By" value={filters.sortBy} onChange={(value) => setFilters({ ...filters, sortBy: value as typeof filters.sortBy })}><option value="created_at">Created At</option><option value="match_score">Match Score</option><option value="deadline">Deadline</option></FilterSelect>
        <div className="flex gap-2 md:col-span-6">
          <button type="submit" className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">Search Jobs</button>
          <button type="button" onClick={() => setFilters({ ...filters, direction: filters.direction === "desc" ? "asc" : "desc" })} className="flex items-center gap-2 rounded-md border border-ink/15 px-3 py-2 text-sm text-ink/70"><ArrowUpDown aria-hidden="true" className="h-4 w-4" /> {filters.direction.toUpperCase()}</button>
        </div>
      </form>
      {error ? <ErrorState message={error} onRetry={loadJobs} /> : null}
      {isLoading ? <p className="text-sm text-ink/60">Loading Jobs...</p> : null}
      {!isLoading && !error && jobs.length === 0 ? <section className="rounded-md border border-dashed border-ink/20 bg-white/70 p-8 text-center"><h2 className="text-lg font-semibold text-ink">No Jobs Yet</h2><p className="mt-2 text-sm text-ink/60">Tailor a resume to automatically add your first job.</p></section> : null}
      {!isLoading && !error && jobs.length > 0 ? (
        <div className="overflow-x-auto rounded-md border border-ink/10 bg-white shadow-sm">
          <table className="w-full min-w-[680px] text-left text-sm"><thead className="border-b border-ink/10 bg-mist/45 text-xs uppercase text-ink/55"><tr><th className="px-4 py-3">Company</th><th className="px-4 py-3">Position</th><th className="px-4 py-3">Score</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Created</th><th className="px-4 py-3">Deadline</th></tr></thead><tbody>{jobs.map((job) => <tr key={job.id} className="border-b border-ink/5 last:border-0 hover:bg-mist/25"><td className="px-4 py-3 font-semibold text-ink"><Link href={`/jobs/${job.id}`}>{job.company ?? "Unknown company"}</Link></td><td className="px-4 py-3 text-ink/70">{job.title ?? "Target role"}</td><td className="px-4 py-3 font-semibold text-leaf">{Math.round(job.match_score)}%</td><td className="px-4 py-3 text-ink/65">{job.status}</td><td className="px-4 py-3 text-ink/55">{formatDate(job.created_at)}</td><td className="px-4 py-3 text-ink/55">{job.deadline ?? "-"}</td></tr>)}</tbody></table>
        </div>
      ) : null}
    </div>
  );
}

function FilterInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label><span className="text-xs font-semibold text-ink/60">{label}</span><input type="number" min="0" max="100" value={value} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 text-sm" /></label>; }
function FilterSelect({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: React.ReactNode }) { return <label><span className="text-xs font-semibold text-ink/60">{label}</span><select value={value} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full rounded-md border border-ink/15 bg-white px-3 py-2 text-sm">{children}</select></label>; }
function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) { return <div className="flex items-center justify-between rounded-md border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral"><span>{message}</span><button type="button" onClick={onRetry} className="flex items-center gap-1 font-semibold"><RefreshCw aria-hidden="true" className="h-4 w-4" /> Retry</button></div>; }
function formatDate(value: string) { return new Date(value).toLocaleDateString(); }
