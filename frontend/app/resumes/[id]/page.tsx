"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, BriefcaseBusiness, Download, RefreshCw } from "lucide-react";
import { ResumeVersionDetail, getResumeVersion, getResumeVersionDownloadUrl } from "@/lib/api";

export default function ResumeVersionDetailPage({ params }: { params: { id: string } }) {
  const [version, setVersion] = useState<ResumeVersionDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const loadVersion = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try { setVersion(await getResumeVersion(params.id)); } catch { setError("Failed to load resume version."); } finally { setIsLoading(false); }
  }, [params.id]);
  useEffect(() => void loadVersion(), [loadVersion]);

  return <div className="space-y-5">
    <Link href="/resumes" className="flex w-fit items-center gap-2 text-sm font-semibold text-leaf"><ArrowLeft aria-hidden="true" className="h-4 w-4" /> Back to Resumes</Link>
    {error ? <ErrorState message={error} onRetry={loadVersion} /> : null}
    {isLoading ? <p className="text-sm text-ink/60">Loading resume version...</p> : null}
    {!isLoading && version ? <>
      <section className="border-b border-ink/10 pb-5"><p className="text-sm font-semibold text-coral">{version.is_base ? "Base Resume" : "Tailored Resume"}</p><h1 className="mt-1 text-3xl font-bold text-ink">{version.name}</h1><p className="mt-2 text-sm text-ink/60">{[version.company, version.job_title, `v${version.version_number}`].filter(Boolean).join(" · ")}</p></section>
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Info label="Role Type" value={version.role_type ?? "Not provided"} /><Info label="Source" value={version.created_from} /><Info label="Created At" value={new Date(version.created_at).toLocaleString()} /><Info label="Match Score" value={`${version.match_score}%`} /></section>
      <div className="flex flex-wrap gap-3">{(["txt", "md", "pdf"] as const).map((format) => <a key={format} href={getResumeVersionDownloadUrl(version.id, format)} className="flex items-center gap-2 rounded-md bg-leaf px-3 py-2 text-sm font-semibold text-white"><Download aria-hidden="true" className="h-4 w-4" /> Download .{format}</a>)}{version.job_id ? <Link href={`/jobs/${version.job_id}`} className="flex items-center gap-2 rounded-md border border-ink/15 bg-white px-3 py-2 text-sm font-semibold text-ink/70"><BriefcaseBusiness aria-hidden="true" className="h-4 w-4" /> Linked Job</Link> : null}</div>
      {!version.is_base ? <DiffSummary summary={version.diff_summary} /> : null}
      <section className="rounded-md border border-ink/10 bg-white p-5"><h2 className="text-lg font-semibold text-ink">Resume Content</h2><pre className="mt-3 max-h-[720px] overflow-auto whitespace-pre-wrap rounded-md bg-ink p-4 text-sm leading-6 text-white">{version.content_text}</pre></section>
    </> : null}
  </div>;
}

function DiffSummary({ summary }: { summary: ResumeVersionDetail["diff_summary"] }) { return <section className="rounded-md border border-ink/10 bg-white p-5"><h2 className="text-lg font-semibold text-ink">Diff Summary</h2><div className="mt-4 grid gap-4 md:grid-cols-2"><List title="Added Keywords" items={summary.added_keywords ?? []} /><List title="Removed or Weakened" items={summary.removed_or_weakened ?? []} /><List title="Reordered" items={summary.reordered_sections ?? []} /><List title="Technology Added" items={summary.technology_changes?.added ?? []} /></div>{summary.rewritten_bullets?.length ? <div className="mt-4"><h3 className="text-sm font-semibold uppercase text-ink/55">Rewritten Bullets</h3>{summary.rewritten_bullets.map((item, index) => <div key={`${item.original}-${index}`} className="mt-3 border-l-2 border-leaf pl-3 text-sm"><p className="text-coral">Original: {item.original}</p><p className="mt-1 text-leaf">New: {item.new}</p></div>)}</div> : null}</section>; }
function List({ title, items }: { title: string; items: string[] }) { return <div><h3 className="text-sm font-semibold uppercase text-ink/55">{title}</h3>{items.length ? <ul className="mt-2 space-y-1 text-sm text-ink/70">{items.map((item) => <li key={item}>- {item}</li>)}</ul> : <p className="mt-2 text-sm text-ink/45">No changes detected.</p>}</div>; }
function Info({ label, value }: { label: string; value: string }) { return <div className="rounded-md border border-ink/10 bg-white p-4 shadow-sm"><p className="text-xs font-semibold uppercase text-ink/50">{label}</p><p className="mt-2 text-sm font-semibold text-ink">{value}</p></div>; }
function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) { return <div className="flex items-center justify-between rounded-md border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral"><span>{message}</span><button type="button" onClick={onRetry} className="flex items-center gap-1 font-semibold"><RefreshCw aria-hidden="true" className="h-4 w-4" /> Retry</button></div>; }
