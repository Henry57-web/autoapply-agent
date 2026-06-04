from fastapi import UploadFile


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


class UnsupportedDocumentError(ValueError):
    pass


async def extract_text_from_upload(file: UploadFile) -> str:
    content = await file.read()
    filename = file.filename or "upload.txt"
    extension = _extension(filename)

    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedDocumentError(f"Unsupported file type: {extension}")

    if extension in {".txt", ".md"}:
        return _decode_text(content)
    if extension == ".pdf":
        return _extract_pdf_text(content)
    if extension == ".docx":
        return _extract_docx_text(content)

    raise UnsupportedDocumentError(f"Unsupported file type: {extension}")


def _extension(filename: str) -> str:
    return "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ".txt"


def _decode_text(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore").strip()


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise UnsupportedDocumentError("PDF parsing requires the pypdf package.") from exc

    from io import BytesIO

    reader = PdfReader(BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _extract_docx_text(content: bytes) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise UnsupportedDocumentError("DOCX parsing requires the python-docx package.") from exc

    from io import BytesIO

    document = Document(BytesIO(content))
    return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
