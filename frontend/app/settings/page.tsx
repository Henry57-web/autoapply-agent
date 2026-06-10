"use client";

import { useCallback, useEffect, useState } from "react";
import { Mail, RefreshCw, ShieldCheck } from "lucide-react";
import { getGmailStatus, GmailConnectionStatus, GmailSyncResult, startGmailOAuth, syncGmail } from "@/lib/api";

export default function SettingsPage() {
  const [status, setStatus] = useState<GmailConnectionStatus | null>(null);
  const [syncResult, setSyncResult] = useState<GmailSyncResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setStatus(await getGmailStatus());
    } catch {
      setError("Failed to load Gmail settings.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => void loadStatus(), [loadStatus]);

  async function connectGmail() {
    setIsConnecting(true);
    setError(null);
    try {
      const oauth = await startGmailOAuth();
      window.location.href = oauth.authorization_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start Gmail connection.");
      setIsConnecting(false);
    }
  }

  async function runSync() {
    setIsSyncing(true);
    setError(null);
    setSyncResult(null);
    try {
      setSyncResult(await syncGmail(30));
      await loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sync Gmail.");
    } finally {
      setIsSyncing(false);
    }
  }

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-3xl font-bold text-ink">Settings</h1>
        <p className="mt-2 text-sm text-ink/60">Connect Gmail with read-only access for application status tracking.</p>
      </section>

      {error ? <ErrorState message={error} onRetry={loadStatus} /> : null}
      {isLoading ? <p className="text-sm text-ink/60">Loading settings...</p> : null}

      {!isLoading && status ? (
        <section className="rounded-md border border-ink/10 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <div className="flex items-center gap-2 text-lg font-semibold text-ink">
                <Mail aria-hidden="true" className="h-5 w-5" />
                Gmail
              </div>
              <p className="mt-2 text-sm text-ink/60">
                Status: <span className="font-semibold text-ink">{status.connected ? "Connected" : "Not connected"}</span>
              </p>
              {status.email_address ? <p className="mt-1 text-sm text-ink/60">{status.email_address}</p> : null}
              {status.last_sync_at ? (
                <p className="mt-1 text-sm text-ink/60">Last sync: {new Date(status.last_sync_at).toLocaleString()}</p>
              ) : null}
              <div className="mt-4 flex items-start gap-2 rounded-md border border-leaf/20 bg-leaf/10 p-3 text-sm text-ink/70">
                <ShieldCheck aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-leaf" />
                <p>Only Gmail read-only permission is requested. The app stores message metadata, snippets, classification, and job links, not full email bodies or attachments.</p>
              </div>
              {status.requires_configuration ? (
                <p className="mt-3 rounded-md border border-coral/30 bg-coral/10 p-3 text-sm text-coral">
                  Gmail OAuth is not fully configured. Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REDIRECT_URI, and GMAIL_TOKEN_ENCRYPTION_KEY in backend/.env.
                </p>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={connectGmail}
                disabled={isConnecting || status.requires_configuration}
                className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isConnecting ? "Connecting..." : status.connected ? "Reconnect Gmail" : "Connect Gmail"}
              </button>
              <button
                type="button"
                onClick={runSync}
                disabled={isSyncing || !status.connected}
                className="flex items-center gap-2 rounded-md border border-ink/15 bg-white px-4 py-2 text-sm font-semibold text-ink disabled:cursor-not-allowed disabled:opacity-50"
              >
                <RefreshCw aria-hidden="true" className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
                {isSyncing ? "Syncing..." : "Sync Gmail"}
              </button>
            </div>
          </div>

          {syncResult ? (
            <div className="mt-5 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
              <MiniStat label="Scanned" value={syncResult.scanned} />
              <MiniStat label="Imported" value={syncResult.imported} />
              <MiniStat label="Updated" value={syncResult.updated} />
              <MiniStat label="Matched" value={syncResult.matched} />
              <MiniStat label="Status Updates" value={syncResult.status_updates} />
              <MiniStat label="Failed" value={syncResult.failed} />
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-ink/10 bg-[#f6f7f3] p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-ink/50">{label}</p>
      <p className="mt-1 text-xl font-bold text-ink">{value}</p>
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
