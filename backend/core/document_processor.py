"""
NJM OS — PDF → LangChain Documents

Extrae texto de PDFs, los divide en chunks y retorna lista de Documents
listos para indexar en ChromaDB.
"""

from __future__ import annotations

import io
from typing import List

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader

_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)


def pdf_to_docs(file_bytes: bytes, filename: str) -> List[Document]:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    chunks = _SPLITTER.split_text(text)
    return [Document(page_content=c, metadata={"source": filename}) for c in chunks]
