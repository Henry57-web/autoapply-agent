import asyncio
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx


MAX_RESPONSE_BYTES = 1_000_000
REQUEST_TIMEOUT_SECONDS = 10
MAX_REDIRECTS = 3
USER_AGENT = "AutoApplyAgent/0.1 local-job-import"


class JobPageFetchError(RuntimeError):
    pass


async def fetch_job_page(url: str) -> str:
    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        ) as client:
            current_url = url
            for _ in range(MAX_REDIRECTS + 1):
                await _validate_public_url(current_url)
                response = await client.get(current_url)
                if not response.is_redirect:
                    break
                redirect_url = response.headers.get("location")
                if not redirect_url:
                    raise JobPageFetchError("The job page returned an invalid redirect.")
                current_url = urljoin(current_url, redirect_url)
            else:
                raise JobPageFetchError("The job page redirected too many times.")
    except httpx.TimeoutException as exc:
        raise JobPageFetchError("The job page timed out.") from exc
    except httpx.HTTPError as exc:
        raise JobPageFetchError("The job page could not be reached.") from exc

    if response.status_code in {401, 403, 429}:
        raise JobPageFetchError("The job page requires login or blocked automated access.")
    if not response.is_success:
        raise JobPageFetchError(f"The job page returned HTTP {response.status_code}.")
    content = response.content
    if len(content) > MAX_RESPONSE_BYTES:
        raise JobPageFetchError("The job page is too large to import safely.")
    html = content.decode(response.encoding or "utf-8", errors="ignore").strip()
    if len(html) < 80:
        raise JobPageFetchError("The job page returned too little content.")
    return html


async def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise JobPageFetchError("Enter a valid HTTP or HTTPS job URL.")
    if parsed.username or parsed.password:
        raise JobPageFetchError("Job URLs with embedded credentials cannot be imported.")
    if parsed.port not in {None, 80, 443}:
        raise JobPageFetchError("Only standard web ports can be imported.")
    hostname = parsed.hostname.lower()
    if hostname == "localhost" or hostname.endswith(".local"):
        raise JobPageFetchError("Local addresses cannot be imported.")
    try:
        addresses = await asyncio.to_thread(socket.getaddrinfo, hostname, parsed.port or 443)
    except socket.gaierror as exc:
        raise JobPageFetchError("The job page hostname could not be resolved.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise JobPageFetchError("Private network addresses cannot be imported.")
