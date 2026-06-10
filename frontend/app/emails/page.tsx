"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { RefreshCw, Search } from "lucide-react";
import {
  EMAIL_TYPES,
  EmailSummary,
  EmailType,
  JobSummary,
  listEmails,
  listJobs,
  syncGmail,
  updateEmail,
} from "@/lib/api";

export default function EmailsPage() {
  const [emails, setEmails] = useState<EmailSummary[]>([]);
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [search, setSearch] = useState("");
  const [emailType, setEmailType] = useState<EmailType | "">("");
  const [unmatchedOnly, setUnmatchedOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [savingEmailId, setSavingEmailId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [emailRows, jobRows] = await Promise.all([
        listEmails({ search, emailType, unmatched: unmatchedOnly }),
        listJobs({ sortBy: "created_at", direction: "desc" }),
      ]);
      setEmails(emailRows);
      setJobs(jobRows);
    } catch {
      setError("Failed to load emails.");
    } finally {
      setIsLoading(false);
    }
  }, [emailType, search, unmatchedOnly]);

  useEffect(() => void loadData(), [loadData]);

  async function runSync() {
    setIsSyncing(true);
    setError(null);
    setSyncMessage(null);
    try {
      const result = await syncGmail(30);
      setSyncMessage(`Scanned ${result.scanned}. Imported ${result.imported}. Matched ${result.matched}. Status updates ${result.status_updates}. Failed ${result.failed}.`);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sync Gmail.");
    } finally {
      setIsSyncing(false);
    }
  }

  async function saveEmail(email: EmailSummary, nextType: EmailType, nextJobId: string) {
    setSavingEmailId(email.id);
    setError(null);
    try {
      const updated = await updateEmail(email.id, {
        email_type: nextType,
        job_id: nextJobId || null,
        clear_job: nextJobId === "",
      });
      setEmails((rows) => rows.map((row) => (row.id === updated.id ? updated : row)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update email.");
    } finally {
      setSavingEmailId(null);
    }
  }

  const counts = useMemo(() => {
    const unmatched = emails.filter((email) => !email.job_id).length;
    return { total: emails.length, unmatched };
  }, [emails]);

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ink">Emails</h1>
          <p className="mt-2 text-sm text-ink/60">Review application emails, classification, and linked jobs.</p>
        </div>
        <button
          type="button"
          onClick={runSync}
          disabled={isSyncing}
          className="flex w-fit items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw aria-hidden="true" className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
          {isSyncing ? "Syncing Gmail..." : "Sync Gmail"}
        </button>
      </section>

      {error ? <ErrorState message={error} onRetry={loadData} /> : null}
      {syncMessage ? <p className="rounded-md border border-leaf/20 bg-leaf/10 px-4 py-3 text-sm text-leaf">{syncMessage}</p> : null}

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MiniStat label="Visible Emails" value={counts.total} />
        <MiniStat label="Unmatched" value={counts.unmatched} />
      </section>

      <section className="rounded-md border border-ink/10 bg-white p-4 shadow-sm">
        <div className="grid gap-3 lg:grid-cols-[1fr_220px_160px_auto]">
          <label className="relative block">
            <Search aria-hidden="true" className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink/35" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search subject, sender, snippet"
              className="w-full rounded-md border border-ink/15 bg-white py-2 pl-9 pr-3 text-sm outline-none focus:border-ink"
            />
          </label>
          <select
            value={emailType}
            onChange={(event) => setEmailType(event.target.value as EmailType | "")}
            className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm outline-none focus:border-ink"
          >
            <option value="">All email types</option>
            {EMAIL_TYPES.map((type) => (
              <option key={type} value={type}>
                {formatType(type)}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 rounded-md border border-ink/15 px-3 py-2 text-sm text-ink/70">
            <input type="checkbox" checked={unmatchedOnly} onChange={(event) => setUnmatchedOnly(event.target.checked)} />
            Unmatched only
          </label>
          <button
            type="button"
            onClick={loadData}
            className="rounded-md border border-ink/15 bg-white px-4 py-2 text-sm font-semibold text-ink"
          >
            Refresh
          </button>
        </div>
      </section>

      {isLoading ? <p className="text-sm text-ink/60">Loading emails...</p> : null}
      {!isLoading && emails.length === 0 ? (
        <section className="rounded-md border border-dashed border-ink/20 bg-white/70 p-8 text-center">
          <h2 className="text-lg font-semibold text-ink">No Emails Yet</h2>
          <p className="mt-2 text-sm text-ink/60">Connect Gmail from Settings, then run a manual sync.</p>
        </section>
      ) : null}

      {!isLoading && emails.length > 0 ? (
        <section className="overflow-hidden rounded-md border border-ink/10 bg-white shadow-sm">
          <div className="grid grid-cols-[1.4fr_180px_220px_180px] gap-3 border-b border-ink/10 bg-[#f6f7f3] px-4 py-3 text-xs font-semibold uppercase tracking-wide text-ink/50 max-lg:hidden">
            <span>Subject</span>
            <span>Type</span>
            <span>Linked Job</span>
            <span>Received</span>
          </div>
          <div className="divide-y divide-ink/10">
            {emails.map((email) => (
              <EmailRow
                key={email.id}
                email={email}
                jobs={jobs}
                isSaving={savingEmailId === email.id}
                onSave={saveEmail}
              />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function EmailRow({
  email,
  jobs,
  isSaving,
  onSave,
}: {
  email: EmailSummary;
  jobs: JobSummary[];
  isSaving: boolean;
  onSave: (email: EmailSummary, nextType: EmailType, nextJobId: string) => Promise<void>;
}) {
  const [nextType, setNextType] = useState<EmailType>(email.email_type);
  const [nextJobId, setNextJobId] = useState(email.job_id ?? "");
  const dirty = nextType !== email.email_type || nextJobId !== (email.job_id ?? "");

  useEffect(() => {
    setNextType(email.email_type);
    setNextJobId(email.job_id ?? "");
  }, [email.email_type, email.job_id]);

  return (
    <div className="grid gap-3 px-4 py-4 lg:grid-cols-[1.4fr_180px_220px_180px] lg:items-start">
      <div>
        <p className="font-semibold text-ink">{email.subject || "No subject"}</p>
        <p className="mt-1 text-xs text-ink/50">{email.sender || "Unknown sender"}</p>
        {email.raw_snippet ? <p className="mt-2 line-clamp-2 text-sm text-ink/65">{email.raw_snippet}</p> : null}
      </div>
      <select
        value={nextType}
        onChange={(event) => setNextType(event.target.value as EmailType)}
        className="rounded-md border border-ink/15 bg-white px-3 py-2 text-sm outline-none focus:border-ink"
      >
        {EMAIL_TYPES.map((type) => (
          <option key={type} value={type}>
            {formatType(type)}
          </option>
        ))}
      </select>
      <div className="space-y-2">
        <select
          value={nextJobId}
          onChange={(event) => setNextJobId(event.target.value)}
          className="w-full rounded-md border border-ink/15 bg-white px-3 py-2 text-sm outline-none focus:border-ink"
        >
          <option value="">No linked job</option>
          {jobs.map((job) => (
            <option key={job.id} value={job.id}>
              {(job.company || "Unknown")} - {(job.title || "Untitled")}
            </option>
          ))}
        </select>
        {email.linked_job ? (
          <Link href={`/jobs/${email.linked_job.id}`} className="block text-xs font-semibold text-leaf hover:underline">
            View linked job
          </Link>
        ) : (
          <span className="block text-xs font-semibold text-coral">Unmatched</span>
        )}
        <button
          type="button"
          disabled={!dirty || isSaving}
          onClick={() => onSave(email, nextType, nextJobId)}
          className="rounded-md bg-ink px-3 py-1.5 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSaving ? "Saving..." : "Save"}
        </button>
      </div>
      <p className="text-sm text-ink/60">{new Date(email.received_at).toLocaleString()}</p>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-ink/10 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink/50">{label}</p>
      <p className="mt-2 text-2xl font-bold text-ink">{value}</p>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral">
      <span>{message}</span>
      <button type="button" onClick={onRetry} className="flex items-center gap-1 font-semibold">
        <RefreshCw aria-hidden="true" className="h-4 w-4" /> Retry
      </button>
    </div>
  );
}

function formatType(type: EmailType) {
  return type.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
}
