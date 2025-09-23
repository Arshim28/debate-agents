#!/usr/bin/env python3

from pdf_converter import MarkdownToPDFConverter
from pathlib import Path
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_to_pdf.py <timestamp>")
        print("Example: python convert_to_pdf.py 20250918_151338")
        return

    timestamp = sys.argv[1]
    output_dir = "outputs"

    converter = MarkdownToPDFConverter()

    try:
        results = converter.convert_debate_outputs(output_dir, timestamp)

        print("PDF Conversion Results:")
        print("=" * 40)

        if results.get('transcript_pdf'):
            print(f"✓ Debate transcript PDF: {results['transcript_pdf']}")
        else:
            print("✗ Failed to convert debate transcript")

        if results.get('synthesis_pdf'):
            print(f"✓ Synthesis report PDF: {results['synthesis_pdf']}")
        else:
            print("✗ Failed to convert synthesis report")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()