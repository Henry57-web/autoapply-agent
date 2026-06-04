import { Save } from "lucide-react";
import type { ResumeSummary } from "@/lib/api";
import { FileField } from "@/components/FileField";

type ResumeManagerProps = {
  file: File | null;
  resumes: ResumeSummary[];
  selectedResumeId: string;
  isSaving: boolean;
  onFileChange: (file: File | null) => void;
  onResumeChange: (resumeId: string) => void;
  onSave: () => void;
};

export function ResumeManager({
  file,
  resumes,
  selectedResumeId,
  isSaving,
  onFileChange,
  onResumeChange,
  onSave,
}: ResumeManagerProps) {
  return (
    <div className="space-y-3">
      {resumes.length > 0 ? (
        <label className="block rounded-md border border-ink/15 bg-white p-4 shadow-sm">
          <span className="block text-sm font-semibold text-ink">Saved Resume</span>
          <select
            value={selectedResumeId}
            onChange={(event) => onResumeChange(event.target.value)}
            className="mt-3 w-full rounded-md border border-ink/15 bg-white px-3 py-2 text-sm text-ink outline-none ring-leaf/25 focus:border-leaf focus:ring-4"
          >
            <option value="">Upload a new resume instead</option>
            {resumes.map((resume) => (
              <option key={resume.id} value={resume.id}>
                {resume.file_name} · {resume.created_at.slice(0, 10)}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {!selectedResumeId ? (
        <>
          <FileField
            id="resume"
            label="Resume"
            helper="Upload your base resume once, then save it for reuse."
            file={file}
            onChange={onFileChange}
          />
          <button
            type="button"
            disabled={!file || isSaving}
            onClick={onSave}
            className="flex w-full items-center justify-center gap-2 rounded-md border border-leaf px-4 py-2 text-sm font-semibold text-leaf transition hover:bg-leaf/5 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Save aria-hidden="true" className="h-4 w-4" />
            {isSaving ? "Saving..." : "Save Resume for Reuse"}
          </button>
        </>
      ) : null}
    </div>
  );
}
