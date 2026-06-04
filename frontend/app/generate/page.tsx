"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import { JobMetadataFields } from "@/components/JobMetadataFields";
import { JobUrlImport } from "@/components/JobUrlImport";
import { ProfileManager } from "@/components/ProfileManager";
import { ResultPanel } from "@/components/ResultPanel";
import { ResumeManager } from "@/components/ResumeManager";
import {
  ApplicationResult,
  CandidateProfileSummary,
  JobMetadata,
  JobImportResult,
  ResumeSummary,
  listCandidateProfiles,
  listResumes,
  runMvpWorkflow,
  saveCandidateProfile,
  saveResume,
} from "@/lib/api";

export default function GeneratePage() {
  const [candidateProfile, setCandidateProfile] = useState<File | null>(null);
  const [savedProfiles, setSavedProfiles] = useState<CandidateProfileSummary[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [resume, setResume] = useState<File | null>(null);
  const [savedResumes, setSavedResumes] = useState<ResumeSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [jobMetadata, setJobMetadata] = useState<Partial<JobMetadata>>({});
  const [result, setResult] = useState<ApplicationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingResume, setIsSavingResume] = useState(false);

  const refreshProfiles = useCallback(async () => {
    try {
      setSavedProfiles(await listCandidateProfiles());
    } catch {
      setError("Failed to load saved profiles.");
    }
  }, []);

  const refreshResumes = useCallback(async () => {
    try {
      setSavedResumes(await listResumes());
    } catch {
      setError("Failed to load saved resumes.");
    }
  }, []);

  useEffect(() => {
    void refreshProfiles();
    void refreshResumes();
  }, [refreshProfiles, refreshResumes]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResult(null);
    if ((!candidateProfile && !selectedProfileId) || (!resume && !selectedResumeId)) {
      setError("Select or upload a candidate profile and resume.");
      return;
    }
    setIsLoading(true);
    try {
      setResult(await runMvpWorkflow({
        candidateProfile,
        candidateProfileId: selectedProfileId,
        resume,
        resumeId: selectedResumeId,
        jobDescription,
        metadata: jobMetadata,
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze and save this job.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSaveProfile() {
    if (!candidateProfile) return;
    setIsSavingProfile(true);
    setError(null);
    try {
      const saved = await saveCandidateProfile(candidateProfile);
      await refreshProfiles();
      setSelectedProfileId(saved.id);
      setCandidateProfile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile.");
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function handleSaveResume() {
    if (!resume) return;
    setIsSavingResume(true);
    setError(null);
    try {
      const saved = await saveResume(resume);
      await refreshResumes();
      setSelectedResumeId(saved.id);
      setResume(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save resume.");
    } finally {
      setIsSavingResume(false);
    }
  }

  function handleJobImported(imported: JobImportResult) {
    setJobMetadata({
      ...jobMetadata,
      company: imported.company,
      title: imported.title,
      job_url: imported.raw_url,
      source: imported.source,
      location: imported.location,
      salary: imported.salary,
      deadline: imported.deadline,
    });
    setJobDescription(imported.description);
  }

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-3xl font-bold text-ink">Tailor Resume</h1>
        <p className="mt-2 text-sm text-ink/60">Analyze a role, generate application materials, and save it to your job pipeline.</p>
      </section>
      {error ? <p className="rounded-md border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral">{error}</p> : null}
      <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
        <form onSubmit={handleSubmit} className="space-y-4">
          <JobUrlImport onImported={handleJobImported} />
          <ProfileManager file={candidateProfile} profiles={savedProfiles} selectedProfileId={selectedProfileId} isSaving={isSavingProfile} onFileChange={setCandidateProfile} onProfileChange={setSelectedProfileId} onSave={handleSaveProfile} />
          <ResumeManager file={resume} resumes={savedResumes} selectedResumeId={selectedResumeId} isSaving={isSavingResume} onFileChange={setResume} onResumeChange={setSelectedResumeId} onSave={handleSaveResume} />
          <section className="rounded-md border border-ink/15 bg-white p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-ink">Job Details</h2>
            <div className="mt-3"><JobMetadataFields value={jobMetadata} onChange={setJobMetadata} showNotes={false} /></div>
          </section>
          <label className="block rounded-md border border-ink/15 bg-white p-4 shadow-sm">
            <span className="block text-sm font-semibold text-ink">Job Description</span>
            <textarea value={jobDescription} onChange={(event) => setJobDescription(event.target.value)} rows={14} className="mt-3 w-full resize-y rounded-md border border-ink/15 px-3 py-3 text-sm leading-6 outline-none focus:border-leaf" placeholder="Paste the full job description here..." />
          </label>
          <button type="submit" disabled={isLoading || !jobDescription.trim()} className="flex w-full items-center justify-center gap-2 rounded-md bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-ink/90 disabled:cursor-not-allowed disabled:bg-ink/40">
            <Sparkles aria-hidden="true" className="h-4 w-4" />
            {isLoading ? "Analyzing and saving job..." : "Generate Tailored Application"}
          </button>
        </form>
        <div>
          {result ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-md border border-leaf/25 bg-leaf/10 px-4 py-3 text-sm text-leaf">
                <span className="font-semibold">Job saved to your pipeline.</span>
                <Link href={`/jobs/${result.job_id}`} className="flex items-center gap-1 font-semibold">View Job <ArrowRight aria-hidden="true" className="h-4 w-4" /></Link>
              </div>
              <ResultPanel result={result} />
            </div>
          ) : (
            <section className="flex min-h-[520px] items-center justify-center rounded-md border border-dashed border-ink/20 bg-white/70 p-8 text-center">
              <div><h2 className="text-xl font-semibold text-ink">Ready for analysis</h2><p className="mt-3 text-sm leading-6 text-ink/60">Your analysis and saved job record will appear here.</p></div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
