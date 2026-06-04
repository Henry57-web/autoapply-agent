type FileFieldProps = {
  id: string;
  label: string;
  helper: string;
  file: File | null;
  onChange: (file: File | null) => void;
};

export function FileField({ id, label, helper, file, onChange }: FileFieldProps) {
  return (
    <label className="block rounded-md border border-ink/15 bg-white p-4 shadow-sm">
      <span className="block text-sm font-semibold text-ink">{label}</span>
      <span className="mt-1 block text-sm text-ink/60">{helper}</span>
      <input
        id={id}
        type="file"
        accept=".txt,.md,.pdf,.docx"
        className="mt-4 block w-full cursor-pointer text-sm text-ink file:mr-4 file:rounded-md file:border-0 file:bg-leaf file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-leaf/90"
        onChange={(event) => onChange(event.target.files?.[0] ?? null)}
      />
      {file ? <span className="mt-3 block truncate text-sm text-leaf">{file.name}</span> : null}
    </label>
  );
}
