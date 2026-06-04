import { JobMetadata } from "@/lib/api";

type JobMetadataFieldsProps = {
  value: Partial<JobMetadata>;
  onChange: (value: Partial<JobMetadata>) => void;
  showNotes?: boolean;
};

export function JobMetadataFields({ value, onChange, showNotes = true }: JobMetadataFieldsProps) {
  function update(field: keyof JobMetadata, fieldValue: string) {
    onChange({ ...value, [field]: fieldValue });
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <MetadataInput label="Company" value={value.company} onChange={(next) => update("company", next)} />
      <MetadataInput label="Position" value={value.title} onChange={(next) => update("title", next)} />
      <MetadataInput label="Job URL" type="url" value={value.job_url} onChange={(next) => update("job_url", next)} />
      <MetadataInput label="Source" value={value.source} onChange={(next) => update("source", next)} placeholder="LinkedIn, referral..." />
      <MetadataInput label="Job Type" value={value.job_type} onChange={(next) => update("job_type", next)} placeholder="Full-time, contract..." />
      <MetadataInput label="Location" value={value.location} onChange={(next) => update("location", next)} />
      <MetadataInput label="Salary" value={value.salary} onChange={(next) => update("salary", next)} placeholder="$120k-$160k" />
      <MetadataInput label="Deadline" type="date" value={value.deadline} onChange={(next) => update("deadline", next)} />
      {showNotes ? (
        <label className="sm:col-span-2">
          <span className="text-xs font-semibold text-ink/70">Notes</span>
          <textarea
            rows={3}
            value={value.notes ?? ""}
            onChange={(event) => update("notes", event.target.value)}
            className="mt-1 w-full resize-y rounded-md border border-ink/15 px-3 py-2 text-sm outline-none focus:border-leaf"
          />
        </label>
      ) : null}
    </div>
  );
}

function MetadataInput({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value?: string | null;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <label>
      <span className="text-xs font-semibold text-ink/70">{label}</span>
      <input
        type={type}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 text-sm outline-none focus:border-leaf"
      />
    </label>
  );
}
