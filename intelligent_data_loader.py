import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document
import logging
from dotenv import load_dotenv
from data_manager import DataManager

logger = logging.getLogger(__name__)

class IntelligentFinancialDataLoader:
    """
    Intelligent data loader that uses multi-modal connectors instead of static markdown files.
    Provides real-time market data, web intelligence, video transcripts, and RAG-based document retrieval.
    """

    def __init__(self):
        load_dotenv()

        # Initialize the data manager with all connectors
        self.data_manager = DataManager(
            open_router_api_key=os.getenv("OPEN_ROUTER_API_KEY"),
            youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
            jina_api_key=os.getenv("JINA_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            summary_collection_name="document_summary",
            chunk_collection_name="document_chunks"
        )

        # Core sector context for intelligent data retrieval
        self.sector_context = {
            "domain": "Indian IT/Technology Sector",
            "focus_areas": [
                "quarterly results and financial performance",
                "AI impact and technological transformation",
                "client spending patterns and demand trends",
                "talent costs and attrition challenges",
                "digital transformation and cloud migration",
                "regulatory changes and compliance impacts",
                "competitive dynamics and market positioning",
                "margin pressures and pricing strategies"
            ],
            "key_companies": [
                "TCS", "Infosys", "Wipro", "HCL Technologies", "Tech Mahindra",
                "Persistent Systems", "Hexaware", "Zensar", "Sonata Software",
                "Happiest Minds", "MapMyIndia"
            ]
        }

        logger.info("Intelligent data loader initialized with multi-modal connectors")

    def get_intelligent_context(self, query_context: str = None) -> str:
        """
        Get intelligent, multi-source context for the current market situation.
        Combines real-time data, historical documents, and web intelligence.
        """
        try:
            # Build comprehensive query for current IT sector state
            base_query = "Current state of Indian IT sector, latest quarterly results, AI impact, and recent developments"
            if query_context:
                base_query = f"{base_query}. Specific focus: {query_context}"

            # Get multi-source data
            logger.info("Fetching multi-source intelligence for IT sector context")
            result = self.data_manager.search(base_query)

            context_parts = [
                "MULTI-SOURCE FINANCIAL INTELLIGENCE:",
                "=" * 60,
                f"Domain: {self.sector_context['domain']}",
                f"Data Sources: {', '.join(result.keys())}",
                "",
                "RECENT MARKET INTELLIGENCE:",
                "=" * 40
            ]

            # Process each data source
            for source_name, data in result.items():
                context_parts.append(f"\n📊 {source_name.upper()}:")
                context_parts.append("-" * 30)

                if source_name == "RAG" and isinstance(data, list):
                    # Process RAG document chunks
                    context_parts.append("Research Document Insights:")
                    for i, chunk in enumerate(data[:3], 1):  # Limit to top 3 chunks
                        context_parts.append(f"{i}. {chunk}")
                        context_parts.append("")

                elif source_name == "Jina Web Connector" and isinstance(data, list):
                    # Process web search results
                    context_parts.append("Current Market News & Analysis:")
                    for i, item in enumerate(data[:3], 1):  # Limit to top 3 results
                        title = item.get('title', 'No title')
                        content = item.get('content', '')[:400]  # Limit content length
                        context_parts.append(f"{i}. {title}")
                        if content:
                            context_parts.append(f"   {content}...")
                        context_parts.append("")

                elif source_name == "YouTube Connector" and isinstance(data, dict):
                    # Process video transcripts
                    context_parts.append("Expert Commentary & Interviews:")
                    for i, (title, transcript) in enumerate(data.items(), 1):
                        if isinstance(transcript, str) and len(transcript) > 100:
                            context_parts.append(f"{i}. {title}")
                            context_parts.append(f"   {transcript[:400]}...")
                            context_parts.append("")

                elif source_name == "Indices Tracker" and isinstance(data, dict):
                    # Process market indices data
                    context_parts.append("Market Index Performance:")
                    for date, value in list(data.items())[:5]:  # Show last 5 data points
                        context_parts.append(f"   {date}: {value}")
                    context_parts.append("")

            context_parts.extend([
                "",
                "KEY SECTOR THEMES TO ANALYZE:",
                "=" * 35
            ])

            for theme in self.sector_context["focus_areas"]:
                context_parts.append(f"• {theme}")

            context_parts.extend([
                "",
                "MAJOR COMPANIES IN SCOPE:",
                "=" * 25,
                ", ".join(self.sector_context["key_companies"]),
                "",
                "=" * 80
            ])

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error getting intelligent context: {e}")
            raise ValueError(f"Failed to get intelligent context: {e}")

    def get_market_data_context(self, indices: List[str] = None, timeframe: str = "3m") -> str:
        """Get specific market data context for indices analysis"""
        try:
            if not indices:
                indices = ["Nifty IT", "Nifty 50", "Nifty Next 50"]

            context_parts = [
                "MARKET DATA CONTEXT:",
                "=" * 30
            ]

            from datetime import datetime, timedelta
            import pandas as pd

            # Calculate date range
            end_date = datetime.now()
            if timeframe == "1m":
                start_date = end_date - timedelta(days=30)
            elif timeframe == "3m":
                start_date = end_date - timedelta(days=90)
            elif timeframe == "6m":
                start_date = end_date - timedelta(days=180)
            else:
                start_date = end_date - timedelta(days=90)

            start_str = start_date.strftime('%d-%b-%Y')
            end_str = end_date.strftime('%d-%b-%Y')

            for index in indices[:1]:  # OPTIMIZATION: Limit to 1 index to reduce API calls
                try:
                    # Use the exact index name as it appears in the API
                    api_index_name = index  # Use exact name: "Nifty IT"

                    data = self.data_manager.indices_connector.get_data(
                        api_index_name, start_str, end_str, "weekly"
                    )
                    if data:
                        context_parts.append(f"\n{index} ({timeframe} performance):")
                        recent_data = list(data.items())[-3:]  # Reduce to last 3 weeks
                        for date, value in recent_data:
                            context_parts.append(f"  {date}: {value}")
                    else:
                        context_parts.append(f"\n{index}: No recent data available")
                except Exception as e:
                    logger.warning(f"Could not fetch data for {index}: {e}")
                    context_parts.append(f"\n{index}: Data unavailable ({str(e)[:50]})")

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error getting market data context: {e}")
            return "Market data temporarily unavailable."

    def search_documents(self, query: str, max_results: int = 5) -> List[str]:
        """Search documents using RAG for specific information"""
        try:
            chunks = self.data_manager.local_docs_connector.retrieve(
                query, chunk_count=max_results
            )
            return chunks if chunks else []
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def get_financial_context(self) -> str:
        """Main method called by agents - provides comprehensive context"""
        return self.get_intelligent_context()

    def get_all_documents(self) -> List[Document]:
        """Legacy compatibility method - returns empty list since we use RAG now"""
        logger.info("get_all_documents called - using RAG retrieval instead")
        return []

    def get_documents_summary(self) -> str:
        """Legacy compatibility method - returns summary"""
        return """Multi-Modal Data Sources:
• ChromaDB RAG System: 11 research documents, 169 chunks
• Nifty Indices Tracker: 143+ Indian market indices
• YouTube Connector: Expert interviews and commentary
• Jina Web Search: Real-time market intelligence
• All data is dynamically retrieved based on query context"""

