from collections.abc import Sequence

import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_pdf_pages(content: bytes) -> list[dict[str, int | str]]:
    try:
        with pymupdf.open(stream=content, filetype="pdf") as pdf:
            if pdf.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")
            pages = [
                {"page_number": page_number, "text": page.get_text("text").strip()}
                for page_number, page in enumerate(pdf, start=1)
            ]
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as exc:
        raise ValueError("The uploaded file is not a readable PDF.") from exc

    text_pages = [page for page in pages if page["text"]]
    if not text_pages:
        raise ValueError("This PDF contains no extractable text; scanned PDFs require OCR.")
    return text_pages


def create_chunks(
    pages: Sequence[dict[str, int | str]],
    chunk_size: int,
    chunk_overlap: int,
) -> list[dict[str, int | str]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=False,
    )
    chunks: list[dict[str, int | str]] = []
    for page in pages:
        for content in splitter.split_text(str(page["text"])):
            chunks.append(
                {
                    "text": content,
                    "page_number": int(page["page_number"]),
                }
            )
    return chunks
