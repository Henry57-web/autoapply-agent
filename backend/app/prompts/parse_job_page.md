Extract job posting fields from the supplied single-page career-site text.

Return JSON only with exactly these keys:
company, title, location, salary, deadline, description, confidence, warnings.

Rules:
- Use null for any missing field.
- Never infer or invent salary or deadline.
- Keep description faithful to the page text.
- confidence must contain company, title, location, salary, deadline, description as numbers from 0 to 1.
- warnings must be a list of short strings for missing or uncertain fields.
