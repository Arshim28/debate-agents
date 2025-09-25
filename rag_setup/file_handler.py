from mistralai import Mistral
from dotenv import load_dotenv
import os 
import base64
import re
import pathlib

class FileHandler:
    def __init__(self, mistral_api_key):
        self.mistral_api_key = mistral_api_key
        self.mistral_client = Mistral(api_key=self.mistral_api_key)
        self.mistral_model = "mistral-ocr-latest"

    def _encode_pdf_to_base64(self, pdf_path):
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        return base64.b64encode(pdf_bytes).decode('utf-8')

    def _get_pages_data(self, pdf_path):
        pdf_base64 = self._encode_pdf_to_base64(pdf_path)
        document_url = f"data:application/pdf;base64,{pdf_base64}"

        ocr_response = self.mistral_client.ocr.process(
            model=self.mistral_model,
            document={
                "type": "document_url",
                "document_url": document_url
            },
            include_image_base64=True
        )

        pages_data = []

        if hasattr(ocr_response, 'pages') and ocr_response.pages:
            for page in ocr_response.pages:
                images = []
                if hasattr(page, 'images') and page.images:
                    for img in page.images:
                        images.append({
                            "id": getattr(img, 'id', ''),
                            "top_left_x": getattr(img, 'top_left_x', 0),
                            "top_left_y": getattr(img, 'top_left_y', 0),
                            "bottom_right_x": getattr(img, 'bottom_right_x', 0),
                            "bottom_right_y": getattr(img, 'bottom_right_y', 0),
                            "image_base64": getattr(img, 'image_base64', None),
                            "image_annotation": getattr(img, 'image_annotation', None)
                        })

                pages_data.append({
                    "index": page.index,
                    "markdown": page.markdown,
                    "images": images
                })
        
            return pages_data
        
        else:
            return []

    def pdf_to_markdown(self, pdf_path, img_dir=None):
        markdown_content = ""
        pages_data = self._get_pages_data(pdf_path)
        for page in pages_data:
            markdown_content += page["markdown"]
            for img in page["images"]:
                if img_dir and img.get("image_base64"):
                    img_path = os.path.join(img_dir, img["id"])
                    os.makedirs(img_dir, exist_ok=True)
                    
                    try:
                        base64_data = img["image_base64"]
                        if base64_data:
                            base64_data = base64_data.strip()
                            if base64_data.startswith('data:'):
                                base64_data = base64_data.split(',', 1)[1]
                            base64_data = re.sub(r'[^A-Za-z0-9+/=]', '', base64_data)
                            decoded_data = base64.b64decode(base64_data)
                            if len(decoded_data) > 0:
                                with open(img_path, "wb") as f:
                                    f.write(decoded_data)
                    except Exception as e:
                        pass
                

        return markdown_content

if __name__ == "__main__":
    load_dotenv()
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    file_handler = FileHandler(mistral_api_key)

    markdown_content = file_handler.pdf_to_markdown(pathlib.Path(__file__).parent.parent / "data_raw/Jefferies-AI Stalls IT Growth Engine-11092025.pdf", pathlib.Path(__file__).parent.parent / "outputs/images")
    with open("outputs/test.md", "w") as f:
        f.write(markdown_content)
