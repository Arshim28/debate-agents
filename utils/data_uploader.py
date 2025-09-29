from openai import OpenAI
from dotenv import load_dotenv
from vector_db_utils import ChromaDB
from file_handler import FileHandler
from gemini_embedding import GeminiEmbedding
import os
import pathlib
from pydantic import BaseModel
import instructor
from google import genai
from google.genai import types
import json

class DataPrepped(BaseModel):
    pdf_title: str
    summary: str
    chunks: list[str]

class ChunkFilter(BaseModel):
    chunks: list[str]

DEBUG = True

class DataUploader:
    def __init__(self, summary_collection_name, chunk_collection_name, gemini_api_key, mistral_api_key, open_router_api_key):
        self.summary_collection_name = summary_collection_name
        self.chunk_collection_name = chunk_collection_name
        self.summary_collection = ChromaDB(summary_collection_name)
        self.chunk_collection = ChromaDB(chunk_collection_name)
        self.file_handler = FileHandler(mistral_api_key)
        self.gemini_embedding = GeminiEmbedding(gemini_api_key)
        # self.instructor = instructor.from_provider("google/gemini-2.5-flash", api_key=gemini_api_key)
        self.gemini_client = genai.Client(api_key=gemini_api_key)

    def _prep_data_for_embedding(self, markdown_content):
        system_prompt = """
        You are given a markdown document extracted from a PDF. The document may contain formatting issues, incomplete text, images, tables, or empty/garbled sections. Your task is to parse the markdown and return a single JSON object (and nothing else) with three fields: pdf_title, summary, and chunks. IMPORTANT: IGNORE all tables, images, charts, and figures — only extract and process TEXT content (paragraphs, headings, bullet points, written analysis).

        The output schema (must be the only output, valid JSON) is:
        {
        "pdf_title": "string",
        "summary": "string",
        "chunks": ["string", "..."]
        }

        Rules:

        1. General behavior
        - Never invent facts or add content not present in the markdown.
        - Summarize and extract only from the given text.
        - Preserve numeric values, currency symbols, percents, LaTeX-style tokens, and inline formatting.
        - Maintain the original logical order of the document.
        - You may merge consecutive related paragraphs if it improves coherence and chunk quality.
        - Do not produce chunks that are just isolated headings without meaningful body text.

        2. pdf_title
        - Generate a concise, informative title that reflects the main subject of the document.
        - Do not copy disclosure/disclaimer text into the title.

        3. Summary
        - Produce a concise descriptive summary of the whole document.
        - Do not hallucinate; summarize only what is present.

        4. Chunking strategy
        - Optimize chunks for both quality and size.
        - Each chunk should be a coherent unit of text (a section, subsection, or group of related paragraphs).
        - Each chunk must be between 100 and 350 words.
        - If a section is shorter than 100 words, you may merge it with an adjacent related section.
        - If a section is longer than 350 words, split it into multiple consecutive chunks, each 100–350 words, keeping the split at natural paragraph boundaries.
        - If a heading has body text and no child headings → create one chunk with the heading + body text (respecting word limits).
        - If a heading has body text and child headings → create one chunk with the heading + body text, then create additional chunks for subheadings (apply the same rules recursively).
        - If a heading has no body text but has child headings → do not create a chunk for the parent heading itself; only recurse into child headings.
        - Skip any section related to disclosur/disclaimer.

        5. Exclusions
        - Completely ignore and exclude:
        - Markdown tables (lines with | symbols),
        - Images, figures, charts, graphs, exhibits,
        - Captions of tables or images.
        - Do not output image markdown (![](...)).
        - Do not attempt to extract binary or non-text content.

        6. Cleaning
        - Remove leading/trailing whitespace from chunk strings but preserve relative line breaks inside the body.
        - Ensure each chunk is informative. Skip chunks with no meaningful text.

        7. Final validation
        - The returned JSON must contain exactly three keys: pdf_title, summary, chunks.
        - chunks must be an array of strings in original order.
        - chunks must exclude disclosure/disclaimer sections. and filler text such as thank-you notes.
        - If no valid chunks exist, return "chunks": [].
        - Output only the JSON object and nothing else.

        """

        input_prompt = f"""
        the extracted markdown is: 
        {markdown_content}
        
        format it in the specified format. Return only a valid JSON 
        """

        response = self.gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DataPrepped,
                system_instruction=system_prompt,
                temperature=0.1,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
            contents=input_prompt
        )
        
        with open(pathlib.Path(__file__).parent.parent / f"outputs/debug.txt", "w") as f:
            f.write(response.text)
        return json.loads(response.text)
    
    def _filter_chunks(self, chunks):
        if len(chunks) <= 90:
            return chunks
        
        print(f"Filtering {len(chunks)} chunks")
        system_prompt = """
        you are given a list of chunks. you need to filter the chunks based on the following rules:
        - the chunks should be meaningful and informative
        - the chunks should not contain the disclosure/disclaimer sections and filler text such as thank-you notes. 
        - the chunks should not contain any non-informative filler text such as thank-you notes
        - the chunks should not contain any tables or images
        - the chunks should only be in english language

        If more than 90 chunks are meaningful and informative then combine similar chunks into one. to bring the count down to 90.

        At the end the number of chunks should be less than 90.

        return the filtered chunks.

        Output format: 
        [chunk1, chunk2, chunk3, ...]
        """

        input_prompt = f"""
        Chunks: {chunks}
        """

        response = self.gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ChunkFilter,
                system_instruction=system_prompt,
                temperature=0.1,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
            contents=input_prompt
        )

        return json.loads(response.text)["chunks"]

    def upload_data(self, pdf_path):
        img_dir = pathlib.Path(__file__).parent.parent / f"outputs/{pdf_path.split('/')[-1].split('.')[0]}/images"
        print("Converting PDF to Markdown")
        markdown_content = self.file_handler.pdf_to_markdown(pdf_path, img_dir)
        if DEBUG:
            with open(pathlib.Path(__file__).parent.parent / f"outputs/{pdf_path.split('/')[-1].split('.')[0]}/markdown.md", "w") as f:
                f.write(markdown_content)

        print("Preparing Data for Embedding")
        formatted_data = self._prep_data_for_embedding(markdown_content)
        if DEBUG:
            with open(pathlib.Path(__file__).parent.parent / f"outputs/{pdf_path.split('/')[-1].split('.')[0]}/formatted_data.json", "w") as f:
                json.dump(formatted_data, f)

        print("Embedding Data")
        summary_embeddings = self.gemini_embedding.embed(formatted_data["summary"])
        chunk_embeddings = self.gemini_embedding.embed(self._filter_chunks(formatted_data["chunks"]))

        print("Uploading Data to ChromaDB")
        # Upload summary
        self.summary_collection.add_chunks(formatted_data["summary"], summary_embeddings, metadatas=[{"source": pdf_path.split('/')[-1].split('.')[0]}])
        
        # Upload chunks using pre-computed batch embeddings (no re-embedding!)
        for i, chunk in enumerate(formatted_data["chunks"]):
            self.chunk_collection.add_chunks(chunk, chunk_embeddings[i], metadatas=[{"source": pdf_path.split('/')[-1].split('.')[0]}])
        print("Data Uploaded Successfully")
        
        with open(pathlib.Path(__file__).parent.parent / "outputs/stats.json", "r") as f:
            stats = json.load(f)

        stats[pdf_path.split('/')[-1].split('.')[0]] = {
            "chunk_count": len(formatted_data["chunks"]),
        }
        with open(pathlib.Path(__file__).parent.parent / "outputs/stats.json", "w") as f:
            json.dump(stats, f, indent=4)

if __name__ == "__main__":
    load_dotenv()
    data_uploader = DataUploader("document_summary", "document_chunks", os.getenv("GEMINI_API_KEY"), os.getenv("MISTRAL_API_KEY"), os.getenv("OPEN_ROUTER_API_KEY"))

    pre_loaded_pdfs = json.loads(open(pathlib.Path(__file__).parent.parent / "outputs/stats.json", "r").read()).keys()

    print(pre_loaded_pdfs)
    for file in os.listdir(pathlib.Path(__file__).parent.parent / "data_raw"):
        if file.endswith(".pdf") and file.split('.')[0] not in pre_loaded_pdfs:
            try:
                print(f"Uploading {file}")
                data_uploader.upload_data(str(pathlib.Path(__file__).parent.parent / "data_raw" / file))
            except Exception as e:
                with open(pathlib.Path(__file__).parent.parent / "outputs/errors.txt", "a") as f:
                    f.write(f"{file}: {e}\n")
                print(f"Error uploading {file}: {e}")
        