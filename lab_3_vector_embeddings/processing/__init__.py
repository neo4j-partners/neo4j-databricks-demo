"""
Processing subpackage for Lab 3: Vector Embeddings and Hybrid Search.

This package handles HTML document parsing, text extraction, and chunking
using neo4j-graphrag's FixedSizeSplitter.
"""

from .document_processor import (
    chunk_document,
    chunk_document_sync,
    classify_document_type,
    extract_entity_references,
    extract_text_from_html,
    process_documents,
    process_documents_sync,
    process_html_content,
    process_html_file,
)

__all__ = [
    "chunk_document",
    "chunk_document_sync",
    "classify_document_type",
    "extract_entity_references",
    "extract_text_from_html",
    "process_documents",
    "process_documents_sync",
    "process_html_content",
    "process_html_file",
]
