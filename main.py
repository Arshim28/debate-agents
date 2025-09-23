import logging
import os
from pathlib import Path
from datetime import datetime
import json

from config import load_config, save_config
from enhanced_orchestrator import EnhancedDebateOrchestrator
from pdf_converter import MarkdownToPDFConverter

def cleanup_old_files():
    """Remove old log files and previous outputs"""
    try:
        # Remove old log file
        log_file = Path('debate.log')
        if log_file.exists():
            log_file.unlink()
            print("Removed old debate.log")

        # Clean up old outputs (keep only last 3 runs)
        outputs_dir = Path('outputs')
        if outputs_dir.exists():
            # Get all files with timestamps
            pattern_files = {}
            for pattern in ['debate_raw_', 'debate_transcript_', 'synthesis_report_']:
                files = list(outputs_dir.glob(f"{pattern}*"))
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                # Keep only the 3 most recent files of each type
                for old_file in files[3:]:
                    old_file.unlink()
                    print(f"Removed old file: {old_file.name}")

    except Exception as e:
        print(f"Warning: Could not clean up old files: {e}")

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('debate.log')
        ]
    )

def save_results(result: dict, output_dir: str = "outputs"):
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Convert DebateMessage objects to dictionaries for JSON serialization
    serializable_result = result.copy()
    if "debate_messages" in serializable_result:
        serializable_result["debate_messages"] = [
            msg.model_dump() if hasattr(msg, 'model_dump') else msg
            for msg in serializable_result["debate_messages"]
        ]

    # Save raw debate data
    with open(f"{output_dir}/debate_raw_{timestamp}.json", 'w', encoding='utf-8') as f:
        json.dump(serializable_result, f, indent=2, default=str, ensure_ascii=False)

    # Save synthesis report
    if result.get("synthesis_report"):
        with open(f"{output_dir}/synthesis_report_{timestamp}.md", 'w', encoding='utf-8') as f:
            f.write(result["synthesis_report"])

    # Save debate transcript
    with open(f"{output_dir}/debate_transcript_{timestamp}.md", 'w', encoding='utf-8') as f:
        f.write("# Dialectical Debate Transcript\n\n")
        f.write(f"**Topic:** {result.get('topic', 'Unknown')}\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Exchanges:** {result.get('total_turns', 0)}\n\n")
        f.write("---\n\n")

        for msg in result.get("debate_messages", []):
            # Handle both DebateMessage objects and dictionaries
            if hasattr(msg, 'model_dump'):
                msg_dict = msg.model_dump()
            else:
                msg_dict = msg

            f.write(f"## Turn {msg_dict['turn_number']} - {msg_dict['agent_name']} ({msg_dict['perspective'].upper()})\n\n")
            f.write(f"{msg_dict['content']}\n\n")
            f.write("---\n\n")

    print(f"Results saved to {output_dir}/ with timestamp {timestamp}")

    # Convert markdown files to PDF
    try:
        print("Converting markdown files to PDF...")
        pdf_converter = MarkdownToPDFConverter()
        pdf_results = pdf_converter.convert_debate_outputs(output_dir, timestamp)

        if pdf_results.get('transcript_pdf'):
            print(f"Debate transcript PDF: {pdf_results['transcript_pdf']}")
        if pdf_results.get('synthesis_pdf'):
            print(f"Synthesis report PDF: {pdf_results['synthesis_pdf']}")

    except Exception as e:
        print(f"Warning: PDF conversion failed: {e}")
        print("Markdown files are still available")

def main():
    print("DIALECTICAL AGENT SYSTEM")
    print("=" * 50)

    # Clean up old files first
    cleanup_old_files()

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        print("Loading configuration...")
        config = load_config()

        # API key is now loaded directly in config.py, no need to check environment variables

        print(f"Configuration loaded successfully")
        print(f"Topic: {config.debate.topic}")
        print(f"Max debate turns: {config.debate.max_debate_turns}")
        print(f"Data directory: {config.debate.data_directory}")

        # Initialize enhanced orchestrator
        print("\nInitializing enhanced multi-agent debate orchestrator...")
        orchestrator = EnhancedDebateOrchestrator(config)

        # Run debate
        print("\nStarting dialectical debate...")
        print("This may take several minutes depending on the model and turn count.")
        print("-" * 50)

        result = orchestrator.run_debate()

        # Display summary
        print("\n" + orchestrator.get_debate_summary(result))

        # Save results
        print("Saving results...")
        save_results(result, config.debate.output_directory)

        if result["status"] == "completed":
            print("\nDEBATE COMPLETED SUCCESSFULLY")
            print("Check the outputs directory for detailed results.")
        else:
            print(f"\nDEBATE FAILED: {result.get('error', 'Unknown error')}")

    except KeyboardInterrupt:
        print("\n\nDebate interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nERROR: {e}")
        print("Check debate.log for detailed error information.")

if __name__ == "__main__":
    main()
