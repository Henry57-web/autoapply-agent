import { FormEvent, useState } from "react";
import { X } from "lucide-react";
import { JobCreateInput } from "@/lib/api";

const EMPTY_JOB: JobCreateInput = { company: "", title: "", description: "" };

export function AddJobDialog({
  isOpen,
  isSaving,
  error,
  onClose,
  onSubmit,
}: {
  isOpen: boolean;
  isSaving: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (input: JobCreateInput) => void;
}) {
  const [form, setForm] = useState<JobCreateInput>(EMPTY_JOB);
  if (!isOpen) return null;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <Modal title="Add Job" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error ? <p className="rounded-md border border-coral/30 bg-coral/10 px-3 py-2 text-sm text-coral">{error}</p> : null}
        <div className="grid gap-3 sm:grid-cols-2">
          <Field required label="Company" value={form.company} onChange={(company) => setForm({ ...form, company })} />
          <Field required label="Title" value={form.title} onChange={(title) => setForm({ ...form, title })} />
          <Field label="Location" value={form.location ?? ""} onChange={(location) => setForm({ ...form, location })} />
          <Field label="Job Type" value={form.job_type ?? ""} onChange={(job_type) => setForm({ ...form, job_type })} />
          <Field label="Source" value={form.source ?? ""} onChange={(source) => setForm({ ...form, source })} />
          <Field label="Salary" value={form.salary ?? ""} onChange={(salary) => setForm({ ...form, salary })} />
          <Field label="URL" type="url" value={form.url ?? ""} onChange={(url) => setForm({ ...form, url })} />
          <Field label="Deadline" type="date" value={form.deadline ?? ""} onChange={(deadline) => setForm({ ...form, deadline })} />
        </div>
        <TextArea label="Description / JD" value={form.description ?? ""} onChange={(description) => setForm({ ...form, description })} />
        <TextArea label="Notes" value={form.notes ?? ""} onChange={(notes) => setForm({ ...form, notes })} />
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-md border border-ink/15 px-4 py-2 text-sm font-semibold text-ink/65">Cancel</button>
          <button disabled={isSaving} type="submit" className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{isSaving ? "Saving Job..." : "Save Job"}</button>
        </div>
      </form>
    </Modal>
  );
}

export function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
      <section role="dialog" aria-modal="true" aria-label={title} className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-md bg-white p-5 shadow-xl">
        <header className="mb-5 flex items-center justify-between">
          <h2 className="text-xl font-bold text-ink">{title}</h2>
          <button type="button" aria-label="Close dialog" onClick={onClose} className="rounded p-1 text-ink/50 hover:bg-mist"><X className="h-5 w-5" /></button>
        </header>
        {children}
      </section>
    </div>
  );
}

function Field({ label, value, type = "text", required, onChange }: { label: string; value: string; type?: string; required?: boolean; onChange: (value: string) => void }) {
  return <label><span className="text-xs font-semibold text-ink/60">{label}</span><input required={required} type={type} value={value} onChange={(event) => onChange(event.target.value)} className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 text-sm" /></label>;
}

function TextArea({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="block"><span className="text-xs font-semibold text-ink/60">{label}</span><textarea value={value} onChange={(event) => onChange(event.target.value)} rows={5} className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 text-sm" /></label>;
}
