"""
Document processing module for Lab 3: Vector Embeddings and Hybrid Search.

This module handles HTML parsing, text extraction, document classification,
and text chunking using neo4j-graphrag FixedSizeSplitter.
"""

import asyncio
import re
import uuid
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)

from .schemas import (
    ChunkConfig,
    DocumentType,
    ProcessedChunk,
    ProcessedDocument,
)


def classify_document_type(filename: str) -> DocumentType:
    """Classify document type based on filename patterns.

    Args:
        filename: HTML filename to classify.

    Returns:
        DocumentType enum value based on filename pattern matching.
    """
    filename_lower = filename.lower()

    if "customer_profile" in filename_lower:
        return DocumentType.CUSTOMER_PROFILE
    if "company_analysis" in filename_lower:
        return DocumentType.COMPANY_ANALYSIS
    if "company_quarterly_report" in filename_lower or "quarterly_report" in filename_lower:
        return DocumentType.COMPANY_REPORT
    if "bank_profile" in filename_lower:
        return DocumentType.BANK_PROFILE
    if "bank_branch" in filename_lower:
        return DocumentType.BANK_BRANCH
    if "investment" in filename_lower and (
        "guide" in filename_lower or "strategy" in filename_lower
    ):
        return DocumentType.INVESTMENT_GUIDE
    if "market_analysis" in filename_lower:
        return DocumentType.MARKET_ANALYSIS
    if "regulatory" in filename_lower or "compliance" in filename_lower:
        return DocumentType.REGULATORY

    return DocumentType.UNKNOWN


def extract_text_from_html(html_content: str) -> tuple[str, str]:
    """Extract clean text and title from HTML content.

    Args:
        html_content: Raw HTML string.

    Returns:
        Tuple of (title, extracted_text).
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Untitled Document"

    # Remove script and style elements
    for element in soup(["script", "style", "head", "meta", "link"]):
        element.decompose()

    # Extract text with paragraph preservation
    text_parts: list[str] = []
    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        text = element.get_text(strip=True)
        if text:
            text_parts.append(text)

    # Join with double newlines to preserve paragraph structure
    extracted_text = "\n\n".join(text_parts)

    # Clean up excessive whitespace while preserving structure
    extracted_text = re.sub(r"\n{3,}", "\n\n", extracted_text)
    extracted_text = re.sub(r" +", " ", extracted_text)

    return title, extracted_text.strip()


def extract_entity_references(
    text: str, document_type: DocumentType
) -> dict[str, list[str]]:
    """Extract entity references from document text.

    Identifies mentions of customers, companies, and stock tickers.

    Args:
        text: Document text to analyze.
        document_type: Type of document for context-aware extraction.

    Returns:
        Dictionary with entity_type keys and lists of identified names/tickers.
    """
    references: dict[str, list[str]] = {
        "customers": [],
        "companies": [],
        "stock_tickers": [],
    }

    # Extract stock tickers (pattern: uppercase letters in parentheses or standalone)
    ticker_pattern = r"\(([A-Z]{2,5})\)|(?<!\w)([A-Z]{2,5})(?=\s|,|\.|$)"
    ticker_matches = re.findall(ticker_pattern, text)
    for match in ticker_matches:
        ticker = match[0] or match[1]
        if ticker and len(ticker) >= 2:
            references["stock_tickers"].append(ticker)

    # Extract company names (common patterns)
    company_patterns = [
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Corp|Corporation|Inc|Company|Ltd|LLC|Solutions|Tech|Bank|Trust|Finance|Holdings))",
        r"((?:First|Second|Global|Pacific|National)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    ]
    for pattern in company_patterns:
        matches = re.findall(pattern, text)
        references["companies"].extend(matches)

    # For customer profiles, extract the customer name from the title/first paragraph
    if document_type == DocumentType.CUSTOMER_PROFILE:
        name_pattern = r"(?:Customer\s+)?(?:Profile[:\s]+)?([A-Z][a-z]+\s+[A-Z][a-z]+)"
        name_matches = re.findall(name_pattern, text[:500])
        references["customers"].extend(name_matches[:1])

    # Remove duplicates while preserving order
    for key in references:
        seen: set[str] = set()
        unique: list[str] = []
        for item in references[key]:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        references[key] = unique

    return references


def process_html_file(
    filepath: Path,
    source_path: str,
) -> ProcessedDocument:
    """Process a single HTML file into a ProcessedDocument.

    Args:
        filepath: Local path to the HTML file.
        source_path: Original path in Databricks volume.

    Returns:
        ProcessedDocument with extracted content and metadata.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()

    filename = filepath.name
    title, raw_text = extract_text_from_html(html_content)
    document_type = classify_document_type(filename)
    entity_refs = extract_entity_references(raw_text, document_type)

    return ProcessedDocument(
        document_id=str(uuid.uuid4()),
        filename=filename,
        document_type=document_type,
        title=title,
        raw_text=raw_text,
        source_path=source_path,
        metadata={
            "char_count": len(raw_text),
            "entity_references": entity_refs,
        },
    )


def process_html_content(
    html_content: str,
    filename: str,
    source_path: str,
) -> ProcessedDocument:
    """Process HTML content string into a ProcessedDocument.

    Args:
        html_content: Raw HTML string.
        filename: Original filename.
        source_path: Original path in Databricks volume.

    Returns:
        ProcessedDocument with extracted content and metadata.
    """
    title, raw_text = extract_text_from_html(html_content)
    document_type = classify_document_type(filename)
    entity_refs = extract_entity_references(raw_text, document_type)

    return ProcessedDocument(
        document_id=str(uuid.uuid4()),
        filename=filename,
        document_type=document_type,
        title=title,
        raw_text=raw_text,
        source_path=source_path,
        metadata={
            "char_count": len(raw_text),
            "entity_references": entity_refs,
        },
    )


async def chunk_document(
    document: ProcessedDocument,
    config: Optional[ChunkConfig] = None,
) -> list[ProcessedChunk]:
    """Split a document into chunks using neo4j-graphrag FixedSizeSplitter.

    Args:
        document: Processed document to chunk.
        config: Chunking configuration. Uses defaults if not provided.

    Returns:
        List of ProcessedChunk objects.
    """
    config = config or ChunkConfig()

    splitter = FixedSizeSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        approximate=config.approximate,
    )

    # Run the async splitter
    text_chunks = await splitter.run(document.raw_text)

    chunks: list[ProcessedChunk] = []
    for text_chunk in text_chunks.chunks:
        chunk = ProcessedChunk(
            chunk_id=text_chunk.uid,
            document_id=document.document_id,
            text=text_chunk.text,
            index=text_chunk.index,
            metadata={
                "document_title": document.title,
                "document_type": document.document_type.value,
                "source_path": document.source_path,
            },
        )
        chunks.append(chunk)

    return chunks


def chunk_document_sync(
    document: ProcessedDocument,
    config: Optional[ChunkConfig] = None,
) -> list[ProcessedChunk]:
    """Synchronous wrapper for chunk_document.

    Args:
        document: Processed document to chunk.
        config: Chunking configuration.

    Returns:
        List of ProcessedChunk objects.
    """
    return asyncio.run(chunk_document(document, config))


async def process_documents(
    html_files: list[tuple[str, str, str]],
    chunk_config: Optional[ChunkConfig] = None,
) -> tuple[list[ProcessedDocument], list[ProcessedChunk]]:
    """Process multiple HTML files into documents and chunks.

    Args:
        html_files: List of tuples (html_content, filename, source_path).
        chunk_config: Chunking configuration.

    Returns:
        Tuple of (documents, all_chunks).
    """
    documents: list[ProcessedDocument] = []
    all_chunks: list[ProcessedChunk] = []

    for html_content, filename, source_path in html_files:
        document = process_html_content(html_content, filename, source_path)
        documents.append(document)

        chunks = await chunk_document(document, chunk_config)
        all_chunks.extend(chunks)

    return documents, all_chunks


def process_documents_sync(
    html_files: list[tuple[str, str, str]],
    chunk_config: Optional[ChunkConfig] = None,
) -> tuple[list[ProcessedDocument], list[ProcessedChunk]]:
    """Synchronous wrapper for process_documents.

    Args:
        html_files: List of tuples (html_content, filename, source_path).
        chunk_config: Chunking configuration.

    Returns:
        Tuple of (documents, all_chunks).
    """
    return asyncio.run(process_documents(html_files, chunk_config))
