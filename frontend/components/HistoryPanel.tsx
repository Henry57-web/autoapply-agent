import { RefreshCw } from "lucide-react";
import {
  APPLICATION_STATUSES,
  ApplicationDetail,
  ApplicationStatus,
  ApplicationSummary,
} from "@/lib/api";
import { ResultPanel } from "@/components/ResultPanel";
import { ApplicationMetadataPanel } from "@/components/ApplicationMetadataPanel";
import { ResumeDiffPanel } from "@/components/ResumeDiffPanel";
import { JobMetadata } from "@/lib/api";

type HistoryPanelProps = {
  applications: ApplicationSummary[];
  selectedApplication: ApplicationDetail | null;
  isLoading: boolean;
  onRefresh: () => void;
  onSelect: (applicationId: string) => void;
  onStatusChange: (status: ApplicationStatus) => void;
  onMetadataSave: (metadata: Partial<JobMetadata>) => Promise<void>;
};

export function HistoryPanel({
  applications,
  selectedApplication,
  isLoading,
  onRefresh,
  onSelect,
  onStatusChange,
  onMetadataSave,
}: HistoryPanelProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
      <aside className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-ink">Application History</h2>
          <button
            type="button"
            onClick={onRefresh}
            title="Refresh applications"
            className="rounded-md border border-ink/15 bg-white p-2 text-ink/65 transition hover:text-leaf"
          >
            <RefreshCw aria-hidden="true" className="h-4 w-4" />
          </button>
        </div>
        {applications.length > 0 ? (
          applications.map((application) => (
            <button
              type="button"
              key={application.id}
              onClick={() => onSelect(application.id)}
              className="block w-full rounded-md border border-ink/10 bg-white p-4 text-left shadow-sm transition hover:border-leaf/50"
            >
              <span className="block text-sm font-semibold text-ink">{application.job_title ?? "Target Role"}</span>
              <span className="mt-1 block text-sm text-ink/60">{application.company_name ?? "Company not detected"}</span>
              {application.metadata?.location || application.metadata?.source ? (
                <span className="mt-1 block text-xs text-ink/45">
                  {[application.metadata?.location, application.metadata?.source].filter(Boolean).join(" · ")}
                </span>
              ) : null}
              <span className="mt-3 flex items-center justify-between text-xs text-ink/55">
                <span>{application.status}</span>
                <span className="font-semibold text-leaf">{Math.round(application.match_score)}%</span>
              </span>
            </button>
          ))
        ) : (
          <p className="rounded-md border border-dashed border-ink/20 bg-white/70 p-4 text-sm leading-6 text-ink/60">
            {isLoading ? "Loading applications..." : "No applications saved yet."}
          </p>
        )}
      </aside>

      <div>
        {selectedApplication ? (
          <div className="space-y-5">
            <section className="flex flex-col gap-3 rounded-md border border-ink/10 bg-white p-4 md:flex-row md:items-center md:justify-between">
              <label className="text-sm font-semibold text-ink">
                Application Status
                <select
                  value={selectedApplication.status}
                  onChange={(event) => onStatusChange(event.target.value as ApplicationStatus)}
                  className="ml-3 rounded-md border border-ink/15 bg-white px-3 py-2 text-sm font-normal outline-none focus:border-leaf"
                >
                  {APPLICATION_STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>
            </section>
            <ApplicationMetadataPanel
              metadata={selectedApplication.metadata}
              missingKeywords={selectedApplication.analysis.missing_keywords}
              onSave={onMetadataSave}
            />
            <ResumeDiffPanel diff={selectedApplication.resume_diff} />
            <ResultPanel result={selectedApplication} />
          </div>
        ) : (
          <section className="flex min-h-[520px] items-center justify-center rounded-md border border-dashed border-ink/20 bg-white/70 p-8 text-center">
            <p className="max-w-sm text-sm leading-6 text-ink/60">Select a saved application to review its materials and status.</p>
          </section>
        )}
      </div>
    </div>
  );
}
