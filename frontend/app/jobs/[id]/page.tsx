"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ExternalLink, FileText, Pencil, RefreshCw } from "lucide-react";
import { JobEditPanel } from "@/components/JobEditPanel";
import { KeywordList } from "@/components/KeywordList";
import { ResumeDiffPanel } from "@/components/ResumeDiffPanel";
import { JOB_STATUSES, JobDetail, JobStatus, JobUpdateInput, getJob, updateJob, updateJobStatus } from "@/lib/api";

export default function JobDetailPage({ params }: { params: { id: string } }) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingStatus, setIsSavingStatus] = useState(false);
  const [isSavingJob, setIsSavingJob] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadJob = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setJob(await getJob(params.id));
    } catch {
      setError("Failed to load job details.");
    } finally {
      setIsLoading(false);
    }
  }, [params.id]);

  useEffect(() => void loadJob(), [loadJob]);

  async function handleStatusChange(status: JobStatus) {
    if (!job) return;
    setIsSavingStatus(true);
    setError(null);
    try {
      setJob(await updateJobStatus(job.id, status));
    } catch {
      setError("Failed to update job status.");
    } finally {
      setIsSavingStatus(false);
    }
  }

  async function handleJobUpdate(input: JobUpdateInput) {
    if (!job) return;
    setIsSavingJob(true);
    setError(null);
    try {
      setJob(await updateJob(job.id, input));
      setIsEditing(false);
    } catch {
      setError("Failed to save job changes.");
    } finally {
      setIsSavingJob(false);
    }
  }

  return (
    <div className="space-y-6">
      <Link href="/jobs" className="flex w-fit items-center gap-2 text-sm font-semibold text-leaf"><ArrowLeft aria-hidden="true" className="h-4 w-4" /> Back to Jobs</Link>
      {error ? <ErrorState message={error} onRetry={loadJob} /> : null}
      {isLoading ? <p className="text-sm text-ink/60">Loading job details...</p> : null}
      {!isLoading && !error && job ? (
        <>
          <section className="flex flex-col gap-4 border-b border-ink/10 pb-5 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-semibold text-coral">{job.company ?? "Unknown company"}</p>
              <h1 className="mt-1 text-3xl font-bold text-ink">{job.title ?? "Target role"}</h1>
              <p className="mt-2 text-sm text-ink/60">{[job.location, job.job_type].filter(Boolean).join(" · ") || "Location not provided"}</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button type="button" onClick={() => setIsEditing((current) => !current)} className="flex items-center gap-2 rounded-md border border-ink/15 bg-white px-3 py-2 text-sm font-semibold text-ink/70">
                <Pencil aria-hidden="true" className="h-4 w-4" /> Edit Job
              </button>
              <label className="text-xs font-semibold uppercase text-ink/55">
                Status
                <select disabled={isSavingStatus} value={job.status} onChange={(event) => void handleStatusChange(event.target.value as JobStatus)} className="ml-3 rounded-md border border-ink/15 bg-white px-3 py-2 text-sm font-normal text-ink">
                  {JOB_STATUSES.map((status) => <option key={status}>{status}</option>)}
                </select>
              </label>
            </div>
          </section>
          {isEditing ? <JobEditPanel job={job} isSaving={isSavingJob} onCancel={() => setIsEditing(false)} onSave={handleJobUpdate} /> : null}
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Info label="Match Score" value={`${job.match_score}%`} />
            <Info label="Salary" value={job.salary ?? "Not provided"} />
            <Info label="Deadline" value={job.deadline ?? "Not provided"} />
            <Info label="Generated At" value={formatDateTime(job.generated_at)} />
          </section>
          <section className="grid gap-3 md:grid-cols-4">
            <Info label="Applied Date" value={formatDateTime(job.applied_at)} />
            <Info label="OA Date" value={formatDateTime(job.oa_received_at)} />
            <Info label="Interview Date" value={formatDateTime(job.interview_at)} />
            <Info label="Offer Date" value={formatDateTime(job.offer_at)} />
          </section>
          {job.resume_version ? <Link href={`/resumes/${job.resume_version.id}`} className="flex w-fit items-center gap-2 rounded-md border border-ink/15 bg-white px-3 py-2 text-sm font-semibold text-leaf"><FileText aria-hidden="true" className="h-4 w-4" /> View linked resume version v{job.resume_version.version_number}</Link> : null}
          {job.url ? <a href={job.url} target="_blank" rel="noreferrer" className="flex w-fit items-center gap-2 text-sm font-semibold text-leaf">Open job posting <ExternalLink aria-hidden="true" className="h-4 w-4" /></a> : null}
          <section className="rounded-md border border-ink/10 bg-white p-5"><h2 className="text-lg font-semibold text-ink">Original Job Description</h2><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-ink/70">{job.description}</p></section>
          <section className="grid gap-4 lg:grid-cols-3">
            <KeywordList title="ATS Keywords" items={job.ats_keywords} emptyText="No ATS keywords detected." />
            <KeywordList title="Missing Skills" items={job.missing_skills} emptyText="No missing skills detected." />
            <KeywordList title="Strengths" items={job.strengths} emptyText="No matched strengths detected." />
          </section>
          <KeywordList title="Weaknesses" items={job.weaknesses} emptyText="No weaknesses detected." />
          {job.analysis ? <section className="rounded-md border border-ink/10 bg-white p-5"><h2 className="text-lg font-semibold text-ink">Analysis Summary</h2><p className="mt-3 text-sm leading-6 text-ink/70">{job.analysis.match_summary}</p></section> : null}
          {job.resume_diff ? <ResumeDiffPanel diff={job.resume_diff} /> : null}
          {job.tailored_resume ? <section className="rounded-md border border-ink/10 bg-white p-5"><h2 className="text-lg font-semibold text-ink">Resume Optimization</h2><h3 className="mt-4 text-sm font-semibold uppercase text-ink/55">Rewritten Bullets</h3><ul className="mt-2 space-y-2">{job.tailored_resume.rewritten_bullets.map((bullet) => <li key={bullet} className="rounded-md bg-mist/60 px-3 py-2 text-sm text-ink/70">{bullet}</li>)}</ul><h3 className="mt-5 text-sm font-semibold uppercase text-ink/55">Tailored Resume</h3><pre className="mt-2 max-h-[560px] overflow-auto whitespace-pre-wrap rounded-md bg-ink p-4 text-sm leading-6 text-white">{job.tailored_resume.ats_optimized_resume}</pre></section> : null}
          {job.cover_letter ? <section className="rounded-md border border-ink/10 bg-white p-5"><h2 className="text-lg font-semibold text-ink">Cover Letter</h2><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-ink/70">{job.cover_letter}</p></section> : null}
          <section className="rounded-md border border-ink/10 bg-white p-5"><h2 className="text-lg font-semibold text-ink">Status History</h2>{job.status_events.length ? <ul className="mt-3 space-y-2">{job.status_events.map((event) => <li key={event.id} className="flex flex-wrap justify-between gap-2 border-b border-ink/5 pb-2 text-sm text-ink/65"><span>{event.from_status ? `${event.from_status} → ` : ""}{event.to_status}</span><span>{formatDateTime(event.created_at)}</span></li>)}</ul> : <p className="mt-2 text-sm text-ink/55">No status events yet.</p>}</section>
        </>
      ) : null}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) { return <div className="rounded-md border border-ink/10 bg-white p-4 shadow-sm"><p className="text-xs font-semibold uppercase text-ink/50">{label}</p><p className="mt-2 text-sm font-semibold text-ink">{value}</p></div>; }
function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) { return <div className="flex items-center justify-between rounded-md border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral"><span>{message}</span><button type="button" onClick={onRetry} className="flex items-center gap-1 font-semibold"><RefreshCw aria-hidden="true" className="h-4 w-4" /> Retry</button></div>; }
function formatDateTime(value: string | null) { return value ? new Date(value).toLocaleString() : "Not recorded"; }
