# Gmail QA Checklist

Use this checklist for local manual verification of Gmail Integration. Do not use production Gmail credentials or commit OAuth secrets.

## 1. Create Google OAuth Client

1. Open Google Cloud Console.
2. Create or select a local development project.
3. Configure the OAuth consent screen.
4. Add yourself as a test user if the app is in testing mode.
5. Create an OAuth client:
   - Application type: Web application
   - Name: AutoApply Agent Local

## 2. Configure Redirect URI

Add this Authorized redirect URI:

```text
http://127.0.0.1:8000/api/v1/gmail/oauth/callback
```

The URI must match `GMAIL_REDIRECT_URI` exactly.

## 3. Generate `GMAIL_TOKEN_ENCRYPTION_KEY`

```bash
cd backend
source .venv/bin/activate
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add the generated value to `backend/.env`.

## 4. Configure Local Environment

In `backend/.env`:

```env
GMAIL_CLIENT_ID=<google-oauth-client-id>
GMAIL_CLIENT_SECRET=<google-oauth-client-secret>
GMAIL_REDIRECT_URI=http://127.0.0.1:8000/api/v1/gmail/oauth/callback
GMAIL_TOKEN_ENCRYPTION_KEY=<generated-fernet-key>
```

Never commit `backend/.env`.

## 5. Start Local Services

```bash
./start.sh
```

Open:

```text
http://localhost:3000/settings
```

## 6. Connect Gmail

1. Click `Connect Gmail`.
2. Sign in with the test Gmail account.
3. Confirm the requested permission is read-only Gmail access.
4. Complete consent and return to `/settings`.
5. Confirm the Gmail status shows connected.

Expected OAuth scope:

```text
https://www.googleapis.com/auth/gmail.readonly
```

No send, modify, delete, or attachment scopes should be requested.

## 7. Sync Gmail

1. Click `Sync Gmail`.
2. Confirm the sync summary appears.
3. Confirm failures, if any, are shown clearly.
4. Go to:

```text
http://localhost:3000/emails
```

## 8. Confirm Emails Appear

Expected:

- Emails list loads without a blank page.
- Subject, sender, type, received time, and linked Job are visible.
- Search and filters work.
- Unmatched emails are clearly marked.

## 9. Confirm Classification

Use recent test emails or forwarded messages with these subjects/snippets:

- `Thank you for applying` -> `APPLICATION_CONFIRMATION`
- `Online Assessment` or `CodeSignal` -> `OA_INVITATION`
- `Interview invitation` -> `INTERVIEW_INVITATION`
- `Unfortunately` or `not move forward` -> `REJECTION`
- `Pleased to offer` -> `OFFER`
- `Recruiter` or `opportunity` -> `RECRUITER_OUTREACH`

Manual override should work when classification is wrong.

## 10. Confirm Job Matching And Status Sync

1. Create or confirm an existing Job with a company name that appears in an email.
2. Sync Gmail.
3. Open `/emails`.
4. Confirm the email is linked to the expected Job.
5. Open the Job Detail page.
6. Confirm status updates:
   - Application confirmation -> `APPLIED`
   - OA invitation -> `OA_RECEIVED`
   - Interview invitation -> `INTERVIEW`
   - Rejection -> `REJECTED`
   - Offer -> `OFFER`
7. Confirm Job Detail shows a new `job_status_events` entry with source `gmail_sync`.

## 11. Manual Override

1. On `/emails`, change `Email Type`.
2. Change `Linked Job`.
3. Save.
4. Confirm the email row updates.
5. Confirm the linked Job status updates when the email type maps to a status.
6. Clear the linked Job and confirm the email becomes unmatched.

## 12. Revoke Gmail Permission

1. Open Google Account settings.
2. Go to Security.
3. Open Third-party apps and services.
4. Remove access for the local AutoApply OAuth client.

## 13. Clear Local Token

Preferred local-only reset:

```bash
cd backend
source .venv/bin/activate
python -m alembic upgrade head
```

Then use a SQL client and run:

```sql
delete from gmail_connections;
delete from emails;
```

Do not print or paste encrypted refresh tokens into chat, logs, commits, or issue trackers.

## 14. Failure Cases To Check

- Missing Gmail environment variables: `/settings` should show configuration is required.
- Not connected: `Sync Gmail` should be disabled or return a clear error.
- Revoked token: sync should fail with a user-readable error.
- No matching Job: email should appear as unmatched.
- Duplicate sync: same Gmail message should update the existing email row, not create duplicates.
