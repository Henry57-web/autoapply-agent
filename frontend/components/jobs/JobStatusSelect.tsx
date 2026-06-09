import { JOB_STATUSES, JobStatus } from "@/lib/api";

export function JobStatusSelect({
  value,
  disabled,
  onChange,
}: {
  value: JobStatus;
  disabled?: boolean;
  onChange: (status: JobStatus) => void;
}) {
  return (
    <select
      aria-label="Move job to status"
      disabled={disabled}
      value={value}
      onChange={(event) => onChange(event.target.value as JobStatus)}
      className="w-full rounded-md border border-ink/15 bg-white px-2 py-1.5 text-xs font-semibold text-ink/70 disabled:opacity-50"
    >
      {JOB_STATUSES.map((status) => <option key={status}>{status}</option>)}
    </select>
  );
}
