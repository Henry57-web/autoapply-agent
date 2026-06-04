import { ResumeDiff } from "@/lib/api";

export function ResumeDiffPanel({ diff }: { diff: ResumeDiff }) {
  return (
    <section className="rounded-md border border-ink/10 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold text-ink">Resume Changes</h3>
        <p className="text-xs text-ink/55">
          <span className="font-semibold text-leaf">+{diff.added_lines}</span> added ·{" "}
          <span className="font-semibold text-coral">-{diff.removed_lines}</span> removed
        </p>
      </div>
      <pre className="mt-3 max-h-[420px] overflow-auto rounded-md border border-ink/10 bg-[#fbfcf9] py-2 text-xs leading-5">
        {diff.lines.map((line, index) => (
          <span
            key={`${line.kind}-${index}`}
            className={`block whitespace-pre-wrap px-3 ${
              line.kind === "added"
                ? "bg-leaf/10 text-leaf"
                : line.kind === "removed"
                  ? "bg-coral/10 text-coral"
                  : "text-ink/55"
            }`}
          >
            {line.kind === "added" ? "+" : line.kind === "removed" ? "-" : " "} {line.text || " "}
          </span>
        ))}
      </pre>
    </section>
  );
}
