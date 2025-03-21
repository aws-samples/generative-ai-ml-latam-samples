import io
from PyPDF2 import PdfReader
from PIL import Image
import io

class PDFDocument:
    """
    A class for reading and extracting text from PDF documents.
    """
    def __init__(self, file_path: str):
        pdf_reader = PdfReader(file_path)
        pages = []
        print(f"Reading {file_path}...")
        for page in pdf_reader.pages:
            pages.append({"text": page.extract_text(), "images": page.images})
        self.pages = pages

    def image_content_block(self, pdf_image):
        image_bytes = pdf_image.data
        image_name = pdf_image.name
        extension = image_name.split('.')[-1]
        if extension == 'jpg':
            extension = 'jpeg'
        
        block = { "image": { "format": extension, "source": { "bytes": image_bytes}}}
        return block

    def text_content_block(self, text):
        return { "text": text }


    def get_content_blocks(self):
        content = []
        current_text = ""

        for page_num,p in enumerate(self.pages):
            page_images = p['images']
            page_text   = p['text']
            if len(page_images) == 0: # Pagina no contiene imagenes.
                current_text += f"PAGE {page_num+1}\n\n {page_text}\n"
            else: # hay imagenes
                current_text += f"PAGE {page_num+1}\n\n {page_text}\n"
                content.append(self.text_content_block(current_text))
                current_text = ""
                for image in page_images:
                    content.append(self.image_content_block(image))
                    #content.append(text_content_block("IMAGE"))

        if current_text != "":
            content.append(self.text_content_block(current_text))

        return content


    def show_images(self):

        for page_number, page in enumerate(self.pages):
            for image in page['images']:
                image_bytes = image.data
                image_name = image.name
                image = Image.open(io.BytesIO(image_bytes))
                print(f"Page {page_number +1}: {image_name}")
                display(image)
    


    def get_images(self):
        
        images = []
        for page_number, page in enumerate(self.pages):
            for image in page['images']:
                image_bytes = image.data
                image_name = image.name
                image = Image.open(io.BytesIO(image_bytes))
                images.append(image)
        return images