import Link from "next/link";
import { CalendarDays, FileCheck2, MapPin } from "lucide-react";
import { JOB_STATUSES, JobStatus, JobSummary } from "@/lib/api";
import { groupJobsByStatus } from "@/lib/job-pipeline";
import { JobStatusSelect } from "@/components/jobs/JobStatusSelect";

export function JobKanban({
  jobs,
  movingJobId,
  onMove,
}: {
  jobs: JobSummary[];
  movingJobId: string | null;
  onMove: (job: JobSummary, status: JobStatus) => void;
}) {
  const groups = groupJobsByStatus(jobs);
  return (
    <div className="overflow-x-auto pb-3">
      <div className="flex min-w-max gap-3">
        {JOB_STATUSES.map((status) => (
          <section
            key={status}
            aria-label={`${status} jobs`}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              const job = jobs.find((item) => item.id === event.dataTransfer.getData("text/job-id"));
              if (job) onMove(job, status);
            }}
            className="w-72 shrink-0 rounded-md border border-ink/10 bg-mist/55 p-3"
          >
            <header className="mb-3 flex items-center justify-between gap-2">
              <h2 className="text-xs font-bold text-ink">{status.replaceAll("_", " ")}</h2>
              <span className="rounded bg-white px-2 py-1 text-xs font-semibold text-ink/55">{groups[status].length}</span>
            </header>
            <div className="min-h-24 space-y-2">
              {groups[status].map((job) => (
                <article
                  key={job.id}
                  draggable={movingJobId !== job.id}
                  onDragStart={(event) => event.dataTransfer.setData("text/job-id", job.id)}
                  className={`rounded-md border border-ink/10 bg-white p-3 shadow-sm ${movingJobId === job.id ? "opacity-50" : "cursor-grab"}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <Link href={`/jobs/${job.id}`} className="block truncate text-sm font-bold text-ink hover:text-leaf">{job.company ?? "Unknown company"}</Link>
                      <p className="mt-1 line-clamp-2 text-xs font-semibold text-ink/65">{job.title ?? "Target role"}</p>
                    </div>
                    <span className={`shrink-0 rounded px-2 py-1 text-xs font-bold ${job.match_score >= 80 ? "bg-leaf/10 text-leaf" : "bg-mist text-ink/65"}`}>{Math.round(job.match_score)}%</span>
                  </div>
                  <p className="mt-3 flex items-center gap-1 text-xs text-ink/50"><MapPin className="h-3.5 w-3.5" /> {job.location ?? "No location"}</p>
                  <p className="mt-1 flex items-center gap-1 text-xs text-ink/50"><CalendarDays className="h-3.5 w-3.5" /> {job.deadline ?? formatDate(job.created_at)}</p>
                  {job.has_resume_version ? <p className="mt-2 flex items-center gap-1 text-xs font-semibold text-leaf"><FileCheck2 className="h-3.5 w-3.5" /> Linked resume</p> : <p className="mt-2 text-xs font-semibold text-coral">No resume version</p>}
                  <div className="mt-3"><JobStatusSelect value={job.status} disabled={movingJobId === job.id} onChange={(next) => onMove(job, next)} /></div>
                </article>
              ))}
              {groups[status].length === 0 ? <p className="rounded-md border border-dashed border-ink/15 p-4 text-center text-xs text-ink/40">No jobs</p> : null}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString();
}
