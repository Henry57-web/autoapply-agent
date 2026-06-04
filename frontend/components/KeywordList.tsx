type KeywordListProps = {
  title: string;
  items: string[];
  emptyText: string;
};

export function KeywordList({ title, items, emptyText }: KeywordListProps) {
  return (
    <section className="rounded-md border border-ink/10 bg-white p-4">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-ink/60">{title}</h3>
      {items.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {items.map((item) => (
            <span key={item} className="rounded-full bg-mist px-3 py-1 text-sm text-ink">
              {item}
            </span>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-ink/55">{emptyText}</p>
      )}
    </section>
  );
}
