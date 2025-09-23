import markdown2
from weasyprint import HTML, CSS
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MarkdownToPDFConverter:
    def __init__(self):
        self.css_style = """
        @page {
            margin: 1in;
            size: A4;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 12pt;
        }

        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            font-size: 24pt;
            margin-top: 30px;
        }

        h2 {
            color: #34495e;
            border-bottom: 2px solid #bdc3c7;
            padding-bottom: 5px;
            font-size: 18pt;
            margin-top: 25px;
        }

        h3 {
            color: #34495e;
            font-size: 14pt;
            margin-top: 20px;
        }

        h4, h5, h6 {
            color: #7f8c8d;
            margin-top: 15px;
        }

        p {
            margin: 10px 0;
            text-align: justify;
        }

        strong {
            color: #2c3e50;
            font-weight: bold;
        }

        em {
            font-style: italic;
            color: #5d6d7e;
        }

        ul, ol {
            margin: 10px 0;
            padding-left: 30px;
        }

        li {
            margin: 5px 0;
        }

        blockquote {
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #f8f9fa;
            font-style: italic;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }

        th, td {
            border: 1px solid #bdc3c7;
            padding: 8px 12px;
            text-align: left;
        }

        th {
            background-color: #ecf0f1;
            font-weight: bold;
            color: #2c3e50;
        }

        hr {
            border: none;
            border-top: 2px solid #bdc3c7;
            margin: 30px 0;
        }

        .page-break {
            page-break-before: always;
        }

        .debate-turn {
            margin: 20px 0;
            padding: 15px;
            border-left: 4px solid #3498db;
            background-color: #f8f9fa;
        }

        .bull-turn {
            border-left-color: #27ae60;
            background-color: #e8f5e8;
        }

        .bear-turn {
            border-left-color: #e74c3c;
            background-color: #fdf2f2;
        }

        .synthesis-section {
            background-color: #f4f6f7;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }

        .metadata {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 10pt;
        }
        """

    def convert_markdown_to_pdf(self, markdown_file: str, output_file: str = None) -> str:
        """Convert a markdown file to PDF"""
        markdown_path = Path(markdown_file)

        if not markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {markdown_file}")

        # Generate output filename if not provided
        if output_file is None:
            output_file = markdown_path.with_suffix('.pdf')

        output_path = Path(output_file)

        try:
            # Read markdown content
            with open(markdown_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Convert markdown to HTML
            html_content = self._convert_to_styled_html(markdown_content, markdown_path.stem)

            # Convert HTML to PDF
            HTML(string=html_content).write_pdf(output_path)

            logger.info(f"Successfully converted {markdown_file} to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error converting {markdown_file} to PDF: {e}")
            raise

    def _convert_to_styled_html(self, markdown_content: str, title: str) -> str:
        """Convert markdown to styled HTML"""
        # Enhanced markdown processing with custom styling
        processed_content = self._preprocess_markdown(markdown_content)

        # Convert to HTML
        html_body = markdown2.markdown(
            processed_content,
            extras=[
                'fenced-code-blocks',
                'tables',
                'header-ids',
                'footnotes',
                'cuddled-lists',
                'metadata',
                'toc'
            ]
        )

        # Create complete HTML document
        html_document = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                {self.css_style}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

        return html_document

    def _preprocess_markdown(self, content: str) -> str:
        """Preprocess markdown content for better PDF formatting"""
        lines = content.split('\n')
        processed_lines = []

        for line in lines:
            # Add CSS classes for debate turns
            if line.startswith('## Turn') and 'BULL' in line:
                processed_lines.append('<div class="debate-turn bull-turn">')
                processed_lines.append(line)
            elif line.startswith('## Turn') and 'BEAR' in line:
                processed_lines.append('<div class="debate-turn bear-turn">')
                processed_lines.append(line)
            elif line.strip() == '---' and processed_lines and 'debate-turn' in str(processed_lines[-10:]):
                processed_lines.append('</div>')
                processed_lines.append(line)
            # Add synthesis section styling
            elif 'synthesis' in line.lower() or 'dialectical analysis' in line.lower():
                processed_lines.append('<div class="synthesis-section">')
                processed_lines.append(line)
            else:
                processed_lines.append(line)

        return '\n'.join(processed_lines)

    def convert_debate_outputs(self, output_dir: str, timestamp: str) -> dict:
        """Convert both debate transcript and synthesis report to PDF"""
        output_path = Path(output_dir)
        results = {}

        # Convert debate transcript
        transcript_file = output_path / f"debate_transcript_{timestamp}.md"
        if transcript_file.exists():
            try:
                pdf_path = self.convert_markdown_to_pdf(
                    str(transcript_file),
                    str(output_path / f"debate_transcript_{timestamp}.pdf")
                )
                results['transcript_pdf'] = pdf_path
                logger.info(f"Debate transcript converted to PDF: {pdf_path}")
            except Exception as e:
                logger.error(f"Failed to convert transcript to PDF: {e}")
                results['transcript_pdf'] = None

        # Convert synthesis report
        synthesis_file = output_path / f"synthesis_report_{timestamp}.md"
        if synthesis_file.exists():
            try:
                pdf_path = self.convert_markdown_to_pdf(
                    str(synthesis_file),
                    str(output_path / f"synthesis_report_{timestamp}.pdf")
                )
                results['synthesis_pdf'] = pdf_path
                logger.info(f"Synthesis report converted to PDF: {pdf_path}")
            except Exception as e:
                logger.error(f"Failed to convert synthesis to PDF: {e}")
                results['synthesis_pdf'] = None

        return results