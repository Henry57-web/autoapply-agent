"use client";

import { FormEvent, useEffect, useState } from "react";
import { Save, X } from "lucide-react";
import { JobDetail, JobUpdateInput } from "@/lib/api";

type JobEditPanelProps = {
  job: JobDetail;
  isSaving: boolean;
  onCancel: () => void;
  onSave: (input: JobUpdateInput) => Promise<void>;
};

type FormState = {
  company: string;
  title: string;
  location: string;
  jobType: string;
  source: string;
  url: string;
  salary: string;
  deadline: string;
  description: string;
  notes: string;
  matchScore: string;
  atsKeywords: string;
  missingSkills: string;
  strengths: string;
  weaknesses: string;
  appliedAt: string;
  oaReceivedAt: string;
  interviewAt: string;
  offerAt: string;
};

export function JobEditPanel({ job, isSaving, onCancel, onSave }: JobEditPanelProps) {
  const [form, setForm] = useState<FormState>(() => toFormState(job));

  useEffect(() => setForm(toFormState(job)), [job]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSave({
      company: optional(form.company),
      title: optional(form.title),
      location: optional(form.location),
      job_type: optional(form.jobType),
      source: optional(form.source),
      url: optional(form.url),
      salary: optional(form.salary),
      deadline: optional(form.deadline),
      description: form.description.trim(),
      notes: optional(form.notes),
      match_score: Number(form.matchScore),
      ats_keywords: toList(form.atsKeywords),
      missing_skills: toList(form.missingSkills),
      strengths: toList(form.strengths),
      weaknesses: toList(form.weaknesses),
      applied_at: toIsoString(form.appliedAt),
      oa_received_at: toIsoString(form.oaReceivedAt),
      interview_at: toIsoString(form.interviewAt),
      offer_at: toIsoString(form.offerAt),
    });
  }

  function update(field: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <section className="rounded-md border border-leaf/30 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">Edit Job</h2>
          <p className="mt-1 text-sm text-ink/55">Update the saved job record. Empty optional fields will be cleared.</p>
        </div>
        <button type="button" onClick={onCancel} className="flex items-center gap-2 rounded-md border border-ink/15 px-3 py-2 text-sm font-semibold text-ink/65">
          <X aria-hidden="true" className="h-4 w-4" /> Cancel
        </button>
      </div>
      <form onSubmit={handleSubmit} className="mt-5 space-y-5">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Input label="Company" value={form.company} onChange={(value) => update("company", value)} />
          <Input label="Position" value={form.title} onChange={(value) => update("title", value)} />
          <Input label="Location" value={form.location} onChange={(value) => update("location", value)} />
          <Input label="Job Type" value={form.jobType} onChange={(value) => update("jobType", value)} />
          <Input label="Source" value={form.source} onChange={(value) => update("source", value)} />
          <Input label="Salary" value={form.salary} onChange={(value) => update("salary", value)} />
          <Input label="Deadline" type="date" value={form.deadline} onChange={(value) => update("deadline", value)} />
          <Input label="Match Score" type="number" min="0" max="100" step="0.01" value={form.matchScore} onChange={(value) => update("matchScore", value)} />
          <Input label="Job URL" type="url" value={form.url} onChange={(value) => update("url", value)} />
        </div>
        <Textarea label="Job Description" rows={10} required value={form.description} onChange={(value) => update("description", value)} />
        <Textarea label="Notes" rows={3} value={form.notes} onChange={(value) => update("notes", value)} />
        <div className="grid gap-4 md:grid-cols-2">
          <Textarea label="ATS Keywords" hint="One item per line" rows={6} value={form.atsKeywords} onChange={(value) => update("atsKeywords", value)} />
          <Textarea label="Missing Skills" hint="One item per line" rows={6} value={form.missingSkills} onChange={(value) => update("missingSkills", value)} />
          <Textarea label="Strengths" hint="One item per line" rows={6} value={form.strengths} onChange={(value) => update("strengths", value)} />
          <Textarea label="Weaknesses" hint="One item per line" rows={6} value={form.weaknesses} onChange={(value) => update("weaknesses", value)} />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Input label="Applied Date" type="datetime-local" value={form.appliedAt} onChange={(value) => update("appliedAt", value)} />
          <Input label="OA Date" type="datetime-local" value={form.oaReceivedAt} onChange={(value) => update("oaReceivedAt", value)} />
          <Input label="Interview Date" type="datetime-local" value={form.interviewAt} onChange={(value) => update("interviewAt", value)} />
          <Input label="Offer Date" type="datetime-local" value={form.offerAt} onChange={(value) => update("offerAt", value)} />
        </div>
        <button type="submit" disabled={isSaving || !form.description.trim()} className="flex items-center gap-2 rounded-md bg-leaf px-4 py-2 text-sm font-semibold text-white disabled:bg-leaf/40">
          <Save aria-hidden="true" className="h-4 w-4" /> {isSaving ? "Saving Job..." : "Save Changes"}
        </button>
      </form>
    </section>
  );
}

function Input({ label, value, onChange, type = "text", min, max, step }: { label: string; value: string; onChange: (value: string) => void; type?: string; min?: string; max?: string; step?: string }) {
  return <label className="text-sm font-semibold text-ink/65">{label}<input type={type} min={min} max={max} step={step} value={value} onChange={(event) => onChange(event.target.value)} className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 text-sm font-normal text-ink" /></label>;
}

function Textarea({ label, value, onChange, rows, hint, required = false }: { label: string; value: string; onChange: (value: string) => void; rows: number; hint?: string; required?: boolean }) {
  return <label className="block text-sm font-semibold text-ink/65">{label}{hint ? <span className="ml-2 text-xs font-normal text-ink/45">{hint}</span> : null}<textarea required={required} rows={rows} value={value} onChange={(event) => onChange(event.target.value)} className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 text-sm font-normal leading-6 text-ink" /></label>;
}

function toFormState(job: JobDetail): FormState {
  return {
    company: job.company ?? "",
    title: job.title ?? "",
    location: job.location ?? "",
    jobType: job.job_type ?? "",
    source: job.source ?? "",
    url: job.url ?? "",
    salary: job.salary ?? "",
    deadline: job.deadline ?? "",
    description: job.description,
    notes: job.notes ?? "",
    matchScore: String(job.match_score),
    atsKeywords: job.ats_keywords.join("\n"),
    missingSkills: job.missing_skills.join("\n"),
    strengths: job.strengths.join("\n"),
    weaknesses: job.weaknesses.join("\n"),
    appliedAt: toLocalDateTime(job.applied_at),
    oaReceivedAt: toLocalDateTime(job.oa_received_at),
    interviewAt: toLocalDateTime(job.interview_at),
    offerAt: toLocalDateTime(job.offer_at),
  };
}

function optional(value: string) { return value.trim() || null; }
function toList(value: string) { return value.split("\n").map((item) => item.trim()).filter(Boolean); }
function toIsoString(value: string) { return value ? new Date(value).toISOString() : null; }
function toLocalDateTime(value: string | null) {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}
