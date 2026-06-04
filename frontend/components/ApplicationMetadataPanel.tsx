"use client";

import { FormEvent, useEffect, useState } from "react";
import { Save } from "lucide-react";
import {
  JobMetadata,
  MISSING_SKILL_CATEGORIES,
  MissingSkillCategory,
} from "@/lib/api";
import { JobMetadataFields } from "@/components/JobMetadataFields";

export function ApplicationMetadataPanel({
  metadata,
  missingKeywords,
  onSave,
}: {
  metadata: JobMetadata;
  missingKeywords: string[];
  onSave: (metadata: Partial<JobMetadata>) => Promise<void>;
}) {
  const [draft, setDraft] = useState<JobMetadata>(metadata);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => setDraft(metadata), [metadata]);

  function updateCategory(keyword: string, category: MissingSkillCategory) {
    setDraft({
      ...draft,
      missing_skill_categories: { ...draft.missing_skill_categories, [keyword]: category },
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    try {
      await onSave(draft);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 rounded-md border border-ink/10 bg-white p-4 shadow-sm">
      <div>
        <h3 className="text-sm font-semibold text-ink">Job Details</h3>
        <div className="mt-3">
          <JobMetadataFields value={draft} onChange={(next) => setDraft({ ...draft, ...next })} />
        </div>
      </div>
      <div>
        <h3 className="text-sm font-semibold text-ink">Missing Skill Review</h3>
        {missingKeywords.length ? (
          <div className="mt-3 space-y-2">
            {missingKeywords.map((keyword) => (
              <label key={keyword} className="flex flex-col gap-1 rounded border border-ink/10 px-3 py-2 sm:flex-row sm:items-center sm:justify-between">
                <span className="text-sm text-ink">{keyword}</span>
                <select
                  value={draft.missing_skill_categories[keyword] ?? "not_on_resume"}
                  onChange={(event) => updateCategory(keyword, event.target.value as MissingSkillCategory)}
                  className="rounded border border-ink/15 bg-white px-2 py-1 text-xs outline-none focus:border-leaf"
                >
                  {MISSING_SKILL_CATEGORIES.map((category) => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-sm text-ink/55">No missing ATS keywords detected.</p>
        )}
      </div>
      <button
        type="submit"
        disabled={isSaving}
        className="flex items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-ink/90 disabled:bg-ink/40"
      >
        <Save aria-hidden="true" className="h-4 w-4" />
        {isSaving ? "Saving..." : "Save Details"}
      </button>
    </form>
  );
}
