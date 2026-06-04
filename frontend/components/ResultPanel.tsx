import type { ApplicationResult } from "@/lib/api";
import { KeywordList } from "@/components/KeywordList";
import { Download } from "lucide-react";
import { getApplicationExportUrl } from "@/lib/api";

type ResultPanelProps = {
  result: ApplicationResult;
};

export function ResultPanel({ result }: ResultPanelProps) {
  const { analysis, tailored_resume: tailoredResume } = result;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-[220px_1fr]">
        <div className="rounded-md border border-ink/10 bg-white p-5">
          <p className="text-sm font-semibold text-ink/60">Match Score</p>
          <p className="mt-2 text-5xl font-bold text-leaf">{Math.round(analysis.match_score)}%</p>
          <p className="mt-3 text-sm text-ink/65">
            {analysis.job_title ?? "Target role"}
            {analysis.company_name ? ` at ${analysis.company_name}` : ""}
          </p>
        </div>
        <div className="rounded-md border border-ink/10 bg-white p-5">
          <h2 className="text-xl font-semibold text-ink">JD Analysis</h2>
          <p className="mt-3 text-sm leading-6 text-ink/75">{analysis.match_summary}</p>
        </div>
      </section>

      <section className="flex flex-wrap gap-2">
        <ExportLink href={getApplicationExportUrl(result.application_id, "resume")} label="Download Resume DOCX" />
        <ExportLink href={getApplicationExportUrl(result.application_id, "cover-letter")} label="Download Cover Letter DOCX" />
      </section>

      <section className="rounded-md border border-ink/10 bg-white p-5">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-ink">Score Breakdown</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-ink/65">
              {analysis.match_score_breakdown.explanation}
            </p>
          </div>
          <p className="text-sm font-semibold text-leaf">
            Total: {formatScore(analysis.match_score_breakdown.total_score)}%
          </p>
        </div>
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          {analysis.match_score_breakdown.categories.map((category) => (
            <div key={category.key} className="rounded-md border border-ink/10 bg-mist/35 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-ink">{category.label}</h3>
                  <p className="mt-1 text-xs text-ink/55">
                    {category.matched_count}/{category.total_count} matched · {formatScore(category.weight)}% weight
                  </p>
                </div>
                <p className="text-lg font-bold text-leaf">{formatScore(category.score)}%</p>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-ink/10">
                <div
                  className="h-full bg-leaf"
                  style={{ width: `${Math.min(100, Math.max(0, category.score))}%` }}
                />
              </div>
              <p className="mt-3 text-xs font-semibold text-ink/60">
                Adds {formatScore(category.contribution)} points to the total score
              </p>
              <KeywordSummary title="Matched" items={category.matched_keywords} />
              <KeywordSummary title="Missing" items={category.missing_keywords} />
            </div>
          ))}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        <KeywordList title="Required Skills" items={analysis.required_skills} emptyText="No required skills found." />
        <KeywordList title="ATS Keywords" items={analysis.ats_keywords} emptyText="No ATS keywords found." />
        <KeywordList title="Missing Keywords" items={analysis.missing_keywords} emptyText="No obvious keyword gaps." />
      </div>

      <section className="rounded-md border border-ink/10 bg-white p-5">
        <h2 className="text-xl font-semibold text-ink">{tailoredResume.headline}</h2>
        <p className="mt-3 text-sm leading-6 text-ink/75">{tailoredResume.summary}</p>
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-ink/60">Rewritten Bullets</h3>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-ink/75">
              {tailoredResume.rewritten_bullets.map((bullet) => (
                <li key={bullet} className="rounded-md bg-mist/70 px-3 py-2">
                  {bullet}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-ink/60">ATS Resume</h3>
            <pre className="mt-3 max-h-[520px] overflow-auto whitespace-pre-wrap rounded-md bg-ink p-4 text-sm leading-6 text-white">
              {tailoredResume.ats_optimized_resume}
            </pre>
          </div>
        </div>
      </section>

      <section className="rounded-md border border-ink/10 bg-white p-5">
        <h2 className="text-xl font-semibold text-ink">Cover Letter</h2>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-ink/75">{result.cover_letter}</p>
      </section>
    </div>
  );
}

function KeywordSummary({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink/50">{title}</p>
      <p className="mt-1 text-xs leading-5 text-ink/65">{items.length > 0 ? items.join(", ") : "None"}</p>
    </div>
  );
}

function formatScore(value: number) {
  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}

function ExportLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="flex items-center gap-2 rounded-md border border-leaf px-3 py-2 text-sm font-semibold text-leaf transition hover:bg-leaf/5"
    >
      <Download aria-hidden="true" className="h-4 w-4" />
      {label}
    </a>
  );
}
