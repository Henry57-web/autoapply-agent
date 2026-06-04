import { Save } from "lucide-react";
import type { CandidateProfileSummary } from "@/lib/api";
import { FileField } from "@/components/FileField";

type ProfileManagerProps = {
  file: File | null;
  profiles: CandidateProfileSummary[];
  selectedProfileId: string;
  isSaving: boolean;
  onFileChange: (file: File | null) => void;
  onProfileChange: (profileId: string) => void;
  onSave: () => void;
};

export function ProfileManager({
  file,
  profiles,
  selectedProfileId,
  isSaving,
  onFileChange,
  onProfileChange,
  onSave,
}: ProfileManagerProps) {
  return (
    <div className="space-y-3">
      {profiles.length > 0 ? (
        <label className="block rounded-md border border-ink/15 bg-white p-4 shadow-sm">
          <span className="block text-sm font-semibold text-ink">Saved Candidate Profile</span>
          <select
            value={selectedProfileId}
            onChange={(event) => onProfileChange(event.target.value)}
            className="mt-3 w-full rounded-md border border-ink/15 bg-white px-3 py-2 text-sm text-ink outline-none ring-leaf/25 focus:border-leaf focus:ring-4"
          >
            <option value="">Upload a new profile instead</option>
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.file_name}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {!selectedProfileId ? (
        <>
          <FileField
            id="candidate-profile"
            label="Candidate Profile"
            helper="Upload a profile once, then save it for reuse across applications."
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
            {isSaving ? "Saving..." : "Save Profile for Reuse"}
          </button>
        </>
      ) : null}
    </div>
  );
}
