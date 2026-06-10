"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, RefreshCw } from "lucide-react";
import { DashboardStats, getDashboardStats } from "@/lib/api";

const emptyStats: DashboardStats = {
  total_jobs: 0,
  ready_to_apply: 0,
  applied: 0,
  oa: 0,
  interviews: 0,
  offers: 0,
  rejected: 0,
  average_match_score: 0,
  highest_match_score: 0,
  pending_oa: 0,
  upcoming_interviews: 0,
  new_recruiter_messages: 0,
  unmatched_emails: 0,
  recent_rejections: 0,
  recent_offers: 0,
};

export default function DashboardPage() {
  const [stats, setStats] = useState(emptyStats);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setStats(await getDashboardStats());
    } catch {
      setError("Failed to load dashboard.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => void loadStats(), [loadStats]);

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ink">Dashboard</h1>
          <p className="mt-2 text-sm text-ink/60">Track your job pipeline and focus on the next useful action.</p>
        </div>
        <Link href="/generate" className="flex w-fit items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white">
          Tailor a resume <ArrowRight aria-hidden="true" className="h-4 w-4" />
        </Link>
      </section>

      {error ? <ErrorState message={error} onRetry={loadStats} /> : null}
      {isLoading ? <p className="text-sm text-ink/60">Loading dashboard...</p> : null}
      {!isLoading && !error ? (
        <>
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Total Jobs" value={stats.total_jobs} />
            <StatCard label="Ready To Apply" value={stats.ready_to_apply} />
            <StatCard label="Applied" value={stats.applied} />
            <StatCard label="OA" value={stats.oa} />
            <StatCard label="Interviews" value={stats.interviews} />
            <StatCard label="Offers" value={stats.offers} />
            <StatCard label="Rejected" value={stats.rejected} />
          </section>
          <section className="grid gap-3 sm:grid-cols-2">
            <StatCard label="Average Match Score" value={`${stats.average_match_score}%`} emphasis />
            <StatCard label="Highest Match Score" value={`${stats.highest_match_score}%`} emphasis />
          </section>
          <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard label="Pending OA" value={stats.pending_oa} />
            <StatCard label="Upcoming Interviews" value={stats.upcoming_interviews} />
            <StatCard label="New Recruiter Messages" value={stats.new_recruiter_messages} />
            <StatCard label="Unmatched Emails" value={stats.unmatched_emails} />
            <StatCard label="Recent Rejections" value={stats.recent_rejections} />
            <StatCard label="Recent Offers" value={stats.recent_offers} />
          </section>
          {stats.total_jobs === 0 ? (
            <section className="rounded-md border border-dashed border-ink/20 bg-white/70 p-8 text-center">
              <h2 className="text-lg font-semibold text-ink">No Jobs Yet</h2>
              <p className="mt-2 text-sm text-ink/60">Generate your first tailored application to start the pipeline.</p>
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function StatCard({ label, value, emphasis = false }: { label: string; value: number | string; emphasis?: boolean }) {
  return (
    <div className="rounded-md border border-ink/10 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink/50">{label}</p>
      <p className={`mt-2 font-bold ${emphasis ? "text-3xl text-leaf" : "text-2xl text-ink"}`}>{value}</p>
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
