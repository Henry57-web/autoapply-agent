import { useMemo, useState } from "react";
import { CheckCircle2, RefreshCw, XCircle } from "lucide-react";
import { batchImportJobs, createJob, JobBatchImportItem } from "@/lib/api";
import { Modal } from "@/components/jobs/AddJobDialog";

export function BatchImportDialog({ isOpen, onClose, onSaved }: { isOpen: boolean; onClose: () => void; onSaved: () => void }) {
  const [input, setInput] = useState("");
  const [results, setResults] = useState<JobBatchImportItem[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [isImporting, setIsImporting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const urls = useMemo(() => [...new Set(input.split(/\r?\n/).map((url) => url.trim()).filter(Boolean))], [input]);
  if (!isOpen) return null;

  async function importUrls() {
    if (urls.length === 0 || urls.length > 10) {
      setMessage("Enter between 1 and 10 job URLs, one per line.");
      return;
    }
    setIsImporting(true);
    setMessage(null);
    try {
      const payload = await batchImportJobs(urls);
      setResults(payload.results);
      setSelected(new Set(payload.results.filter(isSavable).map((item) => item.url)));
      const failed = payload.results.filter((item) => !item.success).length;
      setMessage(`Success: ${payload.results.length - failed} · Failed: ${failed}. Review the results before saving.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Batch import failed. Retry or add jobs manually.");
    } finally {
      setIsImporting(false);
    }
  }

  async function saveSelected() {
    const chosen = results.filter((item) => selected.has(item.url) && isSavable(item));
    setIsSaving(true);
    setMessage(null);
    let saved = 0;
    const failures: string[] = [];
    for (const item of chosen) {
      try {
        const preview = item.job_preview!;
        await createJob({ ...preview, company: preview.company!, title: preview.title! });
        saved += 1;
      } catch {
        failures.push(item.url);
      }
    }
    setIsSaving(false);
    setMessage(failures.length ? `${saved} jobs saved. ${failures.length} failed and can be retried.` : `${saved} jobs saved.`);
    if (saved) onSaved();
    if (failures.length === 0 && saved) setSelected(new Set());
  }

  return (
    <Modal title="Batch Import URLs" onClose={onClose}>
      <div className="space-y-4">
        <label className="block"><span className="text-xs font-semibold text-ink/60">Job URLs, one per line (maximum 10)</span><textarea value={input} onChange={(event) => setInput(event.target.value)} rows={6} placeholder={"https://...\nhttps://..."} className="mt-1 w-full rounded-md border border-ink/15 px-3 py-2 text-sm" /></label>
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" disabled={isImporting} onClick={() => void importUrls()} className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{isImporting ? "Importing jobs..." : "Import URLs"}</button>
          {results.length ? <button type="button" disabled={isImporting} onClick={() => void importUrls()} className="flex items-center gap-2 rounded-md border border-ink/15 px-3 py-2 text-sm font-semibold text-ink/65"><RefreshCw className="h-4 w-4" /> Retry Import</button> : null}
          <span className="text-xs text-ink/50">{urls.length}/10 URLs</span>
        </div>
        {message ? <p className="rounded-md border border-ink/10 bg-mist/60 px-3 py-2 text-sm text-ink/70">{message}</p> : null}
        {results.length ? (
          <div className="space-y-2">
            {results.map((item) => (
              <label key={item.url} className="flex gap-3 rounded-md border border-ink/10 p-3">
                <input type="checkbox" disabled={!isSavable(item)} checked={selected.has(item.url)} onChange={(event) => setSelected(toggleSelection(selected, item.url, event.target.checked))} className="mt-1 h-4 w-4" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">{item.success ? <CheckCircle2 className="h-4 w-4 text-leaf" /> : <XCircle className="h-4 w-4 text-coral" />}<p className="truncate text-xs text-ink/45">{item.url}</p></div>
                  {item.job_preview ? <p className="mt-1 text-sm font-semibold text-ink">{item.job_preview.company ?? "Company missing"} · {item.job_preview.title ?? "Title missing"}</p> : null}
                  {item.error ? <p className="mt-1 text-xs text-coral">{item.error}</p> : null}
                  {item.warnings.length ? <p className="mt-1 text-xs text-ink/55">{item.warnings.join(" · ")}</p> : null}
                  {item.success && !isSavable(item) ? <p className="mt-1 text-xs font-semibold text-coral">Company and title are required. Add this job manually.</p> : null}
                </div>
              </label>
            ))}
          </div>
        ) : null}
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-md border border-ink/15 px-4 py-2 text-sm font-semibold text-ink/65">Close</button>
          {results.length ? <button type="button" disabled={isSaving || selected.size === 0} onClick={() => void saveSelected()} className="rounded-md bg-leaf px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{isSaving ? "Saving selected jobs..." : `Confirm & Save (${selected.size})`}</button> : null}
        </div>
      </div>
    </Modal>
  );
}

function isSavable(item: JobBatchImportItem): boolean {
  return Boolean(item.success && item.job_preview?.company?.trim() && item.job_preview?.title?.trim());
}

function toggleSelection(current: Set<string>, url: string, checked: boolean): Set<string> {
  const next = new Set(current);
  if (checked) next.add(url);
  else next.delete(url);
  return next;
}
