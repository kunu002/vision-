#text_extraction.py 
import pytesseract
import easyocr
from PIL import Image
import PyPDF2
from pdf2image import convert_from_bytes
import logging
import os
import numpy as np
import tempfile
import docx

logging.basicConfig(level=logging.DEBUG)

LANGUAGE_MAP = {
    'English': 'en',
    'Marathi': 'mr',
    'Hindi': 'hi',
    'Bengali': 'bn',
    'Assamese': 'as',
    'Meetei': 'mni',
    'Bihari': 'bh',
    'Bhojpuri': 'bho',
    'Oriya': 'ori',
    'Punjabi': 'pan',
    'Tamil': 'tam',
    'Telugu': 'te',
    'Kannada': 'kn',
    'Nepali': 'ne',
    'Urdu': 'ur',
    'Goan': 'gom',
    'Maithili': 'mai',
    'Santali': 'sat',
    'Gujarati': 'guj',
    'Malayalam': 'mal',
    'Pali': 'pi'
}

TESSERACT_LANGUAGES = ['Punjabi', 'Malayalam', 'Gujarati', 'Meetei', 'Oriya', 'Tamil']

def get_language_code(language):
    return LANGUAGE_MAP.get(language, 'eng') 

def is_pdf_valid(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        if len(pdf_reader.pages) > 0:
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error checking PDF validity: {str(e)}")
        return False

def extract_text_with_easyocr(image, reader):
    result = reader.readtext(np.array(image))
    return ' '.join([text[1] for text in result])

def extract_text_with_tesseract(image, lang_code):
    return pytesseract.image_to_string(image, lang=lang_code)


def extract_text_from_docx(file, language):
    """
    Extract text from a .docx file using python-docx
    If text is empty or non-unicode, fallback to OCR
    """
    text_dict = {}
    try:
        doc = docx.Document(file)
        
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        
        if not full_text:
            return extract_text_with_docx_ocr(file, language)
        
        text_dict[1] = '\n'.join(full_text)
        
        return text_dict
    
    except Exception as e:
        logging.error(f"Error processing DOCX: {str(e)}")
        return extract_text_with_docx_ocr(file, language)

def extract_text_with_docx_ocr(file, language):
    """
    Attempt OCR extraction for .docx files by converting to images
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file.write(file.getvalue())
            temp_file_path = temp_file.name
        
        images = convert_docx_to_images(temp_file_path)
        
        os.unlink(temp_file_path)
        
        text_dict = {}
        lang_code = get_language_code(language)
        
        if language in TESSERACT_LANGUAGES:
            for i, image in enumerate(images):
                text = extract_text_with_tesseract(image, lang_code)
                if text.strip():  
                    text_dict[i+1] = text
        else:
            reader = easyocr.Reader([lang_code], gpu=True)
            for i, image in enumerate(images):
                text = extract_text_with_easyocr(image, reader)
                if text.strip():
                    text_dict[i+1] = text
        
        if not text_dict:
            raise ValueError("No text extracted from DOCX via OCR")
        
        return text_dict
    
    except Exception as e:
        logging.error(f"Error processing DOCX with OCR: {str(e)}")
        return {1: f"Error processing DOCX: {str(e)}"}

def convert_docx_to_images(docx_path):
    """
    Convert DOCX to images using libreoffice
    Requires libreoffice to be installed
    """
    import subprocess
    import tempfile
    from PIL import Image
    
    try:
        with tempfile.TemporaryDirectory() as output_dir:
            pdf_path = os.path.join(output_dir, 'converted.pdf')
            subprocess.run([
                'libreoffice', 
                '--headless', 
                '--convert-to', 
                'pdf', 
                '--outdir', 
                output_dir, 
                docx_path
            ], check=True)
            
            pdf_file = open(pdf_path, 'rb')
            images = convert_from_bytes(pdf_file.read())
            pdf_file.close()
            
            return images
    
    except Exception as e:
        logging.error(f"Error converting DOCX to images: {str(e)}")
        return []

def extract_text_from_pdf(file, language):
    text_dict = {}
    
    try:
        logging.debug(f"Starting PDF processing for file: {file.name}")
        
        if not is_pdf_valid(file):
            raise ValueError("The uploaded file is not a valid PDF.")
        
        logging.debug("PDF validity check passed")
        
        file.seek(0)
        pdf_bytes = file.read()
        
        try:
            images = convert_from_bytes(pdf_bytes)
            logging.debug(f"Converted PDF to {len(images)} images")
        except Exception as e:
            raise ValueError(f"Failed to convert PDF to images: {str(e)}")
        
        if not images:
            raise ValueError("No images extracted from PDF")
        
        lang_code = get_language_code(language)
        
        if language in TESSERACT_LANGUAGES:
            for i, image in enumerate(images):
                text = extract_text_with_tesseract(image, lang_code)
                if text.strip():  
                    text_dict[i+1] = text
        else:
            reader = easyocr.Reader([lang_code],gpu=True)
            for i, image in enumerate(images):
                text = extract_text_with_easyocr(image, reader)
                if text.strip():
                    text_dict[i+1] = text
        
        if not text_dict:
            raise ValueError("No text extracted from PDF")
    
    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        return {1: f"Error processing PDF: {str(e)}"}
    
    return text_dict

def extract_text_from_image(file, language):
    try:
        image = Image.open(file)
        lang_code = get_language_code(language)
        
        if language in TESSERACT_LANGUAGES:
            text = extract_text_with_tesseract(image, lang_code)
        else:
            reader = easyocr.Reader([lang_code])
            text = extract_text_with_easyocr(image, reader)
        
        if not text.strip():
            raise ValueError("No text extracted from image")
        
        return {1: text}
    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        return {1: f"Error processing image: {str(e)}"}

def extract_text(file, language):
    file_extension = os.path.splitext(file.name)[1].lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(file, language)
    elif file_extension in ['.png', '.jpg', '.jpeg']:
        return extract_text_from_image(file, language)
    elif file_extension == '.docx':
        return extract_text_from_docx(file, language)
    else:
        return {1: f"Unsupported file type: {file_extension}"}