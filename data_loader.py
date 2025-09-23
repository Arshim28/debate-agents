import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader
import logging

logger = logging.getLogger(__name__)

class FinancialDataLoader:
    def __init__(self, data_directory: str = "data_raw"):
        self.data_directory = Path(data_directory)
        self.documents: List[Document] = []
        self._load_documents()

    def _load_documents(self):
        if not self.data_directory.exists():
            logger.warning(f"Data directory {self.data_directory} does not exist")
            return

        for file_path in self.data_directory.glob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                doc = Document(
                    page_content=content,
                    metadata={
                        "source": str(file_path),
                        "filename": file_path.name,
                        "document_type": "financial_analysis"
                    }
                )
                self.documents.append(doc)
                logger.info(f"Loaded document: {file_path.name}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

    def get_all_documents(self) -> List[Document]:
        return self.documents

    def get_documents_summary(self) -> str:
        if not self.documents:
            return "No financial documents available."

        summary_parts = [
            f"Available Financial Data ({len(self.documents)} documents):",
            "=" * 50
        ]

        for doc in self.documents:
            filename = doc.metadata.get("filename", "Unknown")
            content_preview = doc.page_content[:200].replace('\n', ' ').strip() + "..."
            summary_parts.append(f"📄 {filename}")
            summary_parts.append(f"   Preview: {content_preview}")
            summary_parts.append("")

        return "\n".join(summary_parts)

    def get_financial_context(self) -> str:
        if not self.documents:
            return "No financial data available for analysis."

        context_parts = [
            "FINANCIAL DATA CONTEXT FOR ANALYSIS:",
            "=" * 50,
            ""
        ]

        for doc in self.documents:
            context_parts.append(f"Document: {doc.metadata.get('filename', 'Unknown')}")
            context_parts.append("-" * 30)
            context_parts.append(doc.page_content)
            context_parts.append("")
            context_parts.append("=" * 80)
            context_parts.append("")

        return "\n".join(context_parts)

    def search_documents(self, query: str, max_results: int = 3) -> List[Document]:
        if not self.documents:
            return []

        query_lower = query.lower()
        scored_docs = []

        for doc in self.documents:
            content_lower = doc.page_content.lower()
            score = content_lower.count(query_lower)
            if score > 0:
                scored_docs.append((score, doc))

        scored_docs.sort(reverse=True, key=lambda x: x[0])
        return [doc for _, doc in scored_docs[:max_results]]