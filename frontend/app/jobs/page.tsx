"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowUpDown, Columns3, List, Plus, RefreshCw, Search, Upload } from "lucide-react";
import { AddJobDialog } from "@/components/jobs/AddJobDialog";
import { BatchImportDialog } from "@/components/jobs/BatchImportDialog";
import { JobKanban } from "@/components/jobs/JobKanban";
import { JobsTable } from "@/components/jobs/JobsTable";
import { JOB_STATUSES, JobCreateInput, JobStatus, JobSummary, createJob, listJobs, updateJobStatus } from "@/lib/api";
import { QUICK_FILTERS, QuickFilter, matchesQuickFilter } from "@/lib/job-pipeline";

type ViewMode = "table" | "kanban";
type Filters = { search: string; status: JobStatus | ""; minScore: string; maxScore: string; sortBy: "match_score" | "created_at" | "deadline"; direction: "asc" | "desc" };

export default function JobsPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [filters, setFilters] = useState<Filters>({ search: "", status: "", minScore: "", maxScore: "", sortBy: "created_at", direction: "desc" });
  const [quickFilter, setQuickFilter] = useState<QuickFilter>("all");
  const [view, setView] = useState<ViewMode>("table");
  const [isLoading, setIsLoading] = useState(true);
  const [movingJobId, setMovingJobId] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [isSavingJob, setIsSavingJob] = useState(false);
  const [showBatchImport, setShowBatchImport] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addError, setAddError] = useState<string | null>(null);

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
  const visibleJobs = useMemo(() => jobs.filter((job) => matchesQuickFilter(job, quickFilter)), [jobs, quickFilter]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadJobs();
  }

  async function handleMove(job: JobSummary, status: JobStatus) {
    if (job.status === status || movingJobId) return;
    const previous = jobs;
    setMovingJobId(job.id);
    setError(null);
    setJobs((current) => current.map((item) => item.id === job.id ? { ...item, status } : item));
    try {
      const updated = await updateJobStatus(job.id, status);
      setJobs((current) => current.map((item) => item.id === job.id ? { ...item, ...updated } : item));
    } catch {
      setJobs(previous);
      setError("Failed to move job. The previous status was restored.");
    } finally {
      setMovingJobId(null);
    }
  }

  async function handleCreate(input: JobCreateInput) {
    setIsSavingJob(true);
    setAddError(null);
    try {
      const job = await createJob(input);
      setIsAdding(false);
      router.push(`/jobs/${job.id}`);
    } catch (createError) {
      setAddError(createError instanceof Error ? createError.message : "Failed to save job.");
    } finally {
      setIsSavingJob(false);
    }
  }

  return (
    <div className="space-y-5">
      <section className="flex flex-col gap-4 border-b border-ink/10 pb-5 md:flex-row md:items-end md:justify-between">
        <div><h1 className="text-3xl font-bold text-ink">Jobs Pipeline</h1><p className="mt-2 text-sm text-ink/60">Prioritize opportunities and move each application forward.</p></div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => setShowBatchImport(true)} className="flex items-center gap-2 rounded-md border border-ink/15 bg-white px-3 py-2 text-sm font-semibold text-ink/70"><Upload className="h-4 w-4" /> Batch Import URLs</button>
          <button type="button" onClick={() => setIsAdding(true)} className="flex items-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white"><Plus className="h-4 w-4" /> Add Job</button>
        </div>
      </section>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-md border border-ink/10 bg-white p-1 shadow-sm">
          <ViewButton active={view === "table"} label="Table View" icon={List} onClick={() => setView("table")} />
          <ViewButton active={view === "kanban"} label="Kanban View" icon={Columns3} onClick={() => setView("kanban")} />
        </div>
        <p className="text-sm text-ink/55">{visibleJobs.length} of {jobs.length} jobs shown</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {QUICK_FILTERS.map((item) => <button key={item.value} type="button" onClick={() => setQuickFilter(item.value)} className={`rounded-md border px-3 py-2 text-xs font-semibold ${quickFilter === item.value ? "border-ink bg-ink text-white" : "border-ink/10 bg-white text-ink/60"}`}>{item.label}</button>)}
      </div>

      <form onSubmit={handleSearch} className="grid gap-3 rounded-md border border-ink/10 bg-white p-4 shadow-sm md:grid-cols-6">
        <label className="md:col-span-2"><span className="text-xs font-semibold text-ink/60">Search</span><div className="relative mt-1"><Search aria-hidden="true" className="absolute left-3 top-2.5 h-4 w-4 text-ink/35" /><input value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} className="w-full rounded-md border border-ink/15 py-2 pl-9 pr-3 text-sm" placeholder="Company or position" /></div></label>
        <FilterSelect label="Status" value={filters.status} onChange={(value) => setFilters({ ...filters, status: value as JobStatus | "" })}><option value="">All statuses</option>{JOB_STATUSES.map((status) => <option key={status}>{status}</option>)}</FilterSelect>
        <FilterInput label="Min Score" value={filters.minScore} onChange={(value) => setFilters({ ...filters, minScore: value })} />
        <FilterInput label="Max Score" value={filters.maxScore} onChange={(value) => setFilters({ ...filters, maxScore: value })} />
        <FilterSelect label="Sort By" value={filters.sortBy} onChange={(value) => setFilters({ ...filters, sortBy: value as Filters["sortBy"] })}><option value="created_at">Created At</option><option value="match_score">Match Score</option><option value="deadline">Deadline</option></FilterSelect>
        <div className="flex gap-2 md:col-span-6">
          <button type="submit" className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">Apply Filters</button>
          <button type="button" onClick={() => setFilters({ ...filters, direction: filters.direction === "desc" ? "asc" : "desc" })} className="flex items-center gap-2 rounded-md border border-ink/15 px-3 py-2 text-sm text-ink/70"><ArrowUpDown className="h-4 w-4" /> {filters.direction.toUpperCase()}</button>
        </div>
      </form>

      {error ? <ErrorState message={error} onRetry={loadJobs} /> : null}
      {isLoading ? <p className="text-sm text-ink/60">Loading Jobs...</p> : null}
      {!isLoading && !error && jobs.length === 0 ? <EmptyState onAdd={() => setIsAdding(true)} /> : null}
      {!isLoading && !error && jobs.length > 0 && visibleJobs.length === 0 ? <p className="rounded-md border border-dashed border-ink/20 bg-white/70 p-8 text-center text-sm text-ink/60">No jobs match this filter.</p> : null}
      {!isLoading && visibleJobs.length > 0 ? view === "table" ? <JobsTable jobs={visibleJobs} movingJobId={movingJobId} onMove={(job, status) => void handleMove(job, status)} /> : <JobKanban jobs={visibleJobs} movingJobId={movingJobId} onMove={(job, status) => void handleMove(job, status)} /> : null}

      <AddJobDialog isOpen={isAdding} isSaving={isSavingJob} error={addError} onClose={() => { setIsAdding(false); setAddError(null); }} onSubmit={(input) => void handleCreate(input)} />
      <BatchImportDialog isOpen={showBatchImport} onClose={() => setShowBatchImport(false)} onSaved={() => void loadJobs()} />
    </div>
  );
}

function ViewButton({ active, label, icon: Icon, onClick }: { active: boolean; label: string; icon: typeof List; onClick: () => void }) {
  return <button type="button" onClick={onClick} className={`flex items-center gap-2 rounded px-3 py-2 text-sm font-semibold ${active ? "bg-ink text-white" : "text-ink/55"}`}><Icon className="h-4 w-4" /> {label}</button>;
}
function FilterInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label><span className="text-xs font-semibold text-ink/60">{label}</span><input type="number" min="0" max="100" value={value} onChange={(event) => onChange(event.target.value)} className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 text-sm" /></label>; }
function FilterSelect({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: React.ReactNode }) { return <label><span className="text-xs font-semibold text-ink/60">{label}</span><select value={value} onChange={(event) => onChange(event.target.value)} className="mt-1 w-full rounded-md border border-ink/15 bg-white px-3 py-2 text-sm">{children}</select></label>; }
function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) { return <div className="flex items-center justify-between rounded-md border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral"><span>{message}</span><button type="button" onClick={() => void onRetry()} className="flex items-center gap-1 font-semibold"><RefreshCw className="h-4 w-4" /> Retry</button></div>; }
function EmptyState({ onAdd }: { onAdd: () => void }) { return <section className="rounded-md border border-dashed border-ink/20 bg-white/70 p-8 text-center"><h2 className="text-lg font-semibold text-ink">No Jobs Yet</h2><p className="mt-2 text-sm text-ink/60">Add a job manually or import URLs to start your pipeline.</p><button type="button" onClick={onAdd} className="mt-4 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">Add Job</button></section>; }
