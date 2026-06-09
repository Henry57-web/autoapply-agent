import { JOB_STATUSES, JobStatus, JobSummary } from "@/lib/api";

export type QuickFilter =
  | "all"
  | "high_match"
  | "ready_to_apply"
  | "needs_review"
  | "deadline_soon"
  | "no_resume_version";

export const QUICK_FILTERS: { value: QuickFilter; label: string }[] = [
  { value: "all", label: "All Jobs" },
  { value: "high_match", label: "High Match" },
  { value: "ready_to_apply", label: "Ready To Apply" },
  { value: "needs_review", label: "Needs Review" },
  { value: "deadline_soon", label: "Deadline Soon" },
  { value: "no_resume_version", label: "No Resume Version" },
];

export function groupJobsByStatus(jobs: JobSummary[]): Record<JobStatus, JobSummary[]> {
  const groups = JOB_STATUSES.reduce(
    (result, status) => ({ ...result, [status]: [] }),
    {} as Record<JobStatus, JobSummary[]>,
  );
  for (const job of jobs) groups[job.status].push(job);
  return groups;
}

export function matchesQuickFilter(job: JobSummary, filter: QuickFilter, now = new Date()): boolean {
  if (filter === "high_match") return job.match_score >= 80;
  if (filter === "ready_to_apply") return job.status === "READY_TO_APPLY";
  if (filter === "needs_review") return job.needs_review;
  if (filter === "no_resume_version") return !job.has_resume_version;
  if (filter === "deadline_soon") {
    if (!job.deadline) return false;
    const today = startOfDay(now);
    const deadline = startOfDay(new Date(`${job.deadline}T00:00:00`));
    const daysAway = (deadline.getTime() - today.getTime()) / 86_400_000;
    return daysAway >= 0 && daysAway <= 7;
  }
  return true;
}

function startOfDay(value: Date): Date {
  const result = new Date(value);
  result.setHours(0, 0, 0, 0);
  return result;
}
