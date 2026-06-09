import Link from "next/link";
import { FileCheck2, FileX2 } from "lucide-react";
import { JobStatus, JobSummary } from "@/lib/api";
import { JobStatusSelect } from "@/components/jobs/JobStatusSelect";

export function JobsTable({
  jobs,
  movingJobId,
  onMove,
}: {
  jobs: JobSummary[];
  movingJobId: string | null;
  onMove: (job: JobSummary, status: JobStatus) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-md border border-ink/10 bg-white shadow-sm">
      <table className="w-full min-w-[940px] text-left text-sm">
        <thead className="border-b border-ink/10 bg-mist/45 text-xs uppercase text-ink/55">
          <tr>
            <th className="px-4 py-3">Company</th><th className="px-4 py-3">Position</th>
            <th className="px-4 py-3">Score</th><th className="px-4 py-3">Move To</th>
            <th className="px-4 py-3">Resume</th><th className="px-4 py-3">Created</th>
            <th className="px-4 py-3">Deadline</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id} className="border-b border-ink/5 last:border-0 hover:bg-mist/25">
              <td className="px-4 py-3 font-semibold text-ink"><Link href={`/jobs/${job.id}`}>{job.company ?? "Unknown company"}</Link></td>
              <td className="px-4 py-3 text-ink/70">{job.title ?? "Target role"}</td>
              <td className="px-4 py-3 font-semibold text-leaf">{Math.round(job.match_score)}%</td>
              <td className="w-48 px-4 py-3"><JobStatusSelect value={job.status} disabled={movingJobId === job.id} onChange={(status) => onMove(job, status)} /></td>
              <td className="px-4 py-3 text-ink/55">{job.has_resume_version ? <FileCheck2 aria-label="Linked resume" className="h-4 w-4 text-leaf" /> : <FileX2 aria-label="No linked resume" className="h-4 w-4 text-coral" />}</td>
              <td className="px-4 py-3 text-ink/55">{formatDate(job.created_at)}</td>
              <td className="px-4 py-3 text-ink/55">{job.deadline ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString();
}
