export type JobAnalysis = {
  job_title: string | null;
  company_name: string | null;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  ats_keywords: string[];
  missing_keywords: string[];
  match_score: number;
  match_score_breakdown: MatchScoreBreakdown;
  match_summary: string;
};

export type ScoreCategory = {
  key: string;
  label: string;
  weight: number;
  score: number;
  contribution: number;
  matched_count: number;
  total_count: number;
  matched_keywords: string[];
  missing_keywords: string[];
};

export type MatchScoreBreakdown = {
  total_score: number;
  categories: ScoreCategory[];
  explanation: string;
};

export type TailoredResume = {
  headline: string;
  summary: string;
  rewritten_bullets: string[];
  ats_optimized_resume: string;
};

export type ApplicationResult = {
  application_id: string;
  job_id: string;
  candidate_profile_id: string;
  resume_id: string;
  resume_version_id: string;
  analysis: JobAnalysis;
  tailored_resume: TailoredResume;
  cover_letter: string;
};

export const JOB_STATUSES = [
  "SAVED",
  "READY_TO_APPLY",
  "APPLIED",
  "OA_RECEIVED",
  "OA_COMPLETED",
  "INTERVIEW",
  "REJECTED",
  "OFFER",
  "WITHDRAWN",
  "GHOSTED",
] as const;

export type JobStatus = (typeof JOB_STATUSES)[number];

export type JobSummary = {
  id: string;
  application_id: string | null;
  company: string | null;
  title: string | null;
  location: string | null;
  job_type: string | null;
  source: string | null;
  url: string | null;
  salary: string | null;
  deadline: string | null;
  match_score: number;
  status: JobStatus;
  created_at: string;
  updated_at: string;
};

export type JobDetail = JobSummary & {
  description: string;
  ats_keywords: string[];
  missing_skills: string[];
  strengths: string[];
  weaknesses: string[];
  notes: string | null;
  applied_at: string | null;
  oa_received_at: string | null;
  interview_at: string | null;
  offer_at: string | null;
  generated_at: string;
  analysis: JobAnalysis | null;
  tailored_resume: TailoredResume | null;
  cover_letter: string | null;
  resume_diff: ResumeDiff | null;
  metadata: JobMetadata | null;
  status_events: {
    id: string;
    from_status: string | null;
    to_status: JobStatus;
    source: string;
    created_at: string;
  }[];
  resume_version: ResumeVersionSummary | null;
};

export type ResumeVersionSource = "BASE_UPLOAD" | "TAILORING_RESULT" | "MANUAL_EDIT" | "IMPORT";

export type ResumeVersionSummary = {
  id: string;
  source_resume_id: string;
  job_id: string | null;
  name: string;
  role_type: string | null;
  version_number: number;
  is_base: boolean;
  company: string | null;
  job_title: string | null;
  created_from: ResumeVersionSource;
  match_score: number;
  created_at: string;
  updated_at: string;
};

export type ResumeVersionDetail = ResumeVersionSummary & {
  content_text: string;
  content_json: Record<string, unknown>;
  diff_summary: {
    added_keywords?: string[];
    rewritten_bullets?: { original: string; new: string }[];
    removed_or_weakened?: string[];
    reordered_sections?: string[];
    technology_changes?: { added?: string[]; removed?: string[] };
    line_diff?: ResumeDiff;
  };
  ats_keywords: string[];
};

export type JobUpdateInput = {
  company: string | null;
  title: string | null;
  location: string | null;
  job_type: string | null;
  source: string | null;
  url: string | null;
  salary: string | null;
  deadline: string | null;
  description: string;
  notes: string | null;
  match_score: number;
  ats_keywords: string[];
  missing_skills: string[];
  strengths: string[];
  weaknesses: string[];
  applied_at: string | null;
  oa_received_at: string | null;
  interview_at: string | null;
  offer_at: string | null;
};

export type DashboardStats = {
  total_jobs: number;
  ready_to_apply: number;
  applied: number;
  oa: number;
  interviews: number;
  offers: number;
  rejected: number;
  average_match_score: number;
  highest_match_score: number;
};

export const APPLICATION_STATUSES = [
  "Draft",
  "Ready to Apply",
  "Applied",
  "Interview",
  "Rejected",
  "Offer",
] as const;

export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];

export const MISSING_SKILL_CATEGORIES = [
  { value: "not_on_resume", label: "Not on resume" },
  { value: "can_add", label: "Can add to resume" },
  { value: "learning", label: "Need to learn" },
  { value: "not_relevant", label: "Not relevant" },
] as const;

export type MissingSkillCategory = (typeof MISSING_SKILL_CATEGORIES)[number]["value"];

export type JobMetadata = {
  company: string | null;
  title: string | null;
  job_url: string | null;
  source: string | null;
  job_type: string | null;
  location: string | null;
  salary: string | null;
  deadline: string | null;
  notes: string | null;
  missing_skill_categories: Record<string, MissingSkillCategory>;
};

export type JobImportResult = {
  source: string;
  company: string | null;
  title: string | null;
  location: string | null;
  salary: string | null;
  deadline: string | null;
  description: string;
  confidence: Record<"company" | "title" | "location" | "salary" | "deadline" | "description", number>;
  warnings: string[];
  raw_url: string;
};

export type ResumeDiff = {
  added_lines: number;
  removed_lines: number;
  unchanged_lines: number;
  lines: { kind: "unchanged" | "added" | "removed"; text: string }[];
};

export type CandidateProfileSummary = {
  id: string;
  file_name: string;
  created_at: string;
};

export type ResumeSummary = {
  id: string;
  file_name: string;
  created_at: string;
};

export type ApplicationSummary = {
  id: string;
  job_title: string | null;
  company_name: string | null;
  match_score: number;
  status: ApplicationStatus;
  created_at: string;
  metadata: JobMetadata;
};

export type ApplicationDetail = ApplicationSummary &
  ApplicationResult & {
    job_description: string;
    resume_diff: ResumeDiff;
  };

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function runMvpWorkflow(input: {
  candidateProfile?: File | null;
  candidateProfileId?: string;
  resume?: File | null;
  resumeId?: string;
  jobDescription: string;
  metadata?: Partial<JobMetadata>;
}): Promise<ApplicationResult> {
  const formData = new FormData();
  if (input.candidateProfile) {
    formData.append("candidate_profile", input.candidateProfile);
  } else if (input.candidateProfileId) {
    formData.append("candidate_profile_id", input.candidateProfileId);
  }
  if (input.resume) {
    formData.append("resume", input.resume);
  } else if (input.resumeId) {
    formData.append("resume_id", input.resumeId);
  }
  formData.append("job_description", input.jobDescription);
  for (const field of ["company", "title", "job_url", "source", "job_type", "location", "salary", "deadline", "notes"] as const) {
    const value = input.metadata?.[field];
    if (value) formData.append(field, value);
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/mvp/run`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message = payload?.detail ?? "Unable to analyze this application.";
    throw new Error(typeof message === "string" ? message : "Unable to analyze this application.");
  }

  return response.json();
}

export async function importJobUrl(url: string): Promise<JobImportResult> {
  return request<JobImportResult>("/api/v1/job-import/url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
}

export async function saveCandidateProfile(profile: File): Promise<CandidateProfileSummary> {
  const formData = new FormData();
  formData.append("profile", profile);
  return request<CandidateProfileSummary>("/api/v1/candidate-profiles", {
    method: "POST",
    body: formData,
  });
}

export async function listCandidateProfiles(): Promise<CandidateProfileSummary[]> {
  return request<CandidateProfileSummary[]>("/api/v1/candidate-profiles");
}

export async function saveResume(resume: File): Promise<ResumeSummary> {
  const formData = new FormData();
  formData.append("resume", resume);
  return request<ResumeSummary>("/api/v1/resumes", {
    method: "POST",
    body: formData,
  });
}

export async function listResumes(): Promise<ResumeSummary[]> {
  return request<ResumeSummary[]>("/api/v1/resumes");
}

export async function listApplications(): Promise<ApplicationSummary[]> {
  return request<ApplicationSummary[]>("/api/v1/applications");
}

export async function listJobs(params: {
  search?: string;
  status?: JobStatus | "";
  minScore?: string;
  maxScore?: string;
  sortBy?: "match_score" | "created_at" | "deadline";
  direction?: "asc" | "desc";
} = {}): Promise<JobSummary[]> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.status) query.set("status", params.status);
  if (params.minScore) query.set("min_score", params.minScore);
  if (params.maxScore) query.set("max_score", params.maxScore);
  if (params.sortBy) query.set("sort_by", params.sortBy);
  if (params.direction) query.set("direction", params.direction);
  return request<JobSummary[]>(`/api/v1/jobs${query.size ? `?${query}` : ""}`);
}

export async function getJob(jobId: string): Promise<JobDetail> {
  return request<JobDetail>(`/api/v1/jobs/${jobId}`);
}

export async function updateJobStatus(jobId: string, status: JobStatus): Promise<JobDetail> {
  return request<JobDetail>(`/api/v1/jobs/${jobId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

export async function updateJob(jobId: string, input: JobUpdateInput): Promise<JobDetail> {
  return request<JobDetail>(`/api/v1/jobs/${jobId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>("/api/v1/dashboard");
}

export async function listResumeVersions(params: {
  search?: string;
  roleType?: string;
  company?: string;
  direction?: "asc" | "desc";
} = {}): Promise<ResumeVersionSummary[]> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.roleType) query.set("role_type", params.roleType);
  if (params.company) query.set("company", params.company);
  if (params.direction) query.set("direction", params.direction);
  return request<ResumeVersionSummary[]>(`/api/v1/resume-versions${query.size ? `?${query}` : ""}`);
}

export async function getResumeVersion(versionId: string): Promise<ResumeVersionDetail> {
  return request<ResumeVersionDetail>(`/api/v1/resume-versions/${versionId}`);
}

export async function deleteResumeVersion(versionId: string): Promise<void> {
  await request<void>(`/api/v1/resume-versions/${versionId}`, { method: "DELETE" });
}

export function getResumeVersionDownloadUrl(versionId: string, format: "txt" | "md" | "pdf") {
  return `${API_BASE_URL}/api/v1/resume-versions/${versionId}/download?format=${format}`;
}

export async function getApplication(applicationId: string): Promise<ApplicationDetail> {
  return request<ApplicationDetail>(`/api/v1/applications/${applicationId}`);
}

export async function updateApplicationStatus(
  applicationId: string,
  status: ApplicationStatus,
): Promise<ApplicationSummary> {
  return request<ApplicationSummary>(`/api/v1/applications/${applicationId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

export async function updateApplicationMetadata(
  applicationId: string,
  metadata: Partial<JobMetadata>,
): Promise<ApplicationDetail> {
  return request<ApplicationDetail>(`/api/v1/applications/${applicationId}/metadata`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(metadata),
  });
}

export function getApplicationExportUrl(applicationId: string, document: "resume" | "cover-letter") {
  return `${API_BASE_URL}/api/v1/applications/${applicationId}/export/${document}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? "Request failed.");
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
