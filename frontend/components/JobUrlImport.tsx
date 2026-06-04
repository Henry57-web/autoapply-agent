"use client";

import { useState } from "react";
import { Download, TriangleAlert } from "lucide-react";
import { JobImportResult, importJobUrl } from "@/lib/api";

export function JobUrlImport({ onImported }: { onImported: (result: JobImportResult) => void }) {
  const [url, setUrl] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);

  async function handleImport() {
    setError(null);
    setWarnings([]);
    setIsImporting(true);
    try {
      const result = await importJobUrl(url);
      setWarnings(result.warnings);
      onImported(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "This page could not be imported. Please paste the job description manually.");
    } finally {
      setIsImporting(false);
    }
  }

  return (
    <section className="rounded-md border border-ink/15 bg-white p-4 shadow-sm">
      <h2 className="text-sm font-semibold text-ink">Import from Job URL</h2>
      <div className="mt-3 flex flex-col gap-2 sm:flex-row">
        <input type="url" required value={url} onChange={(event) => setUrl(event.target.value)} className="min-w-0 flex-1 rounded-md border border-ink/15 px-3 py-2 text-sm outline-none focus:border-leaf" placeholder="https://boards.greenhouse.io/..." />
        <button type="button" onClick={handleImport} disabled={isImporting || !url} className="flex items-center justify-center gap-2 rounded-md bg-leaf px-4 py-2 text-sm font-semibold text-white disabled:bg-leaf/40">
          <Download aria-hidden="true" className="h-4 w-4" />
          {isImporting ? "Importing job..." : "Import"}
        </button>
      </div>
      {error ? <p className="mt-3 text-sm text-coral">{error}</p> : null}
      {warnings.length ? <div className="mt-3 space-y-1 text-xs text-coral">{warnings.map((warning) => <p key={warning} className="flex items-start gap-2"><TriangleAlert aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0" />{warning}</p>)}</div> : null}
    </section>
  );
}
