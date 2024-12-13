#translation.py 
from deep_translator import GoogleTranslator, MicrosoftTranslator, MyMemoryTranslator
import time
import requests
from requests.exceptions import RequestException
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANGUAGE_CODE_MAP = {
    'english': 'en',
    'marathi': 'mr',
    'hindi': 'hi',
    'bengali': 'bn',
    'assamese': 'as',
    'meetei': 'mni-Mtei',
    'bihari': 'bh',
    'bhojpuri': 'bho',
    'oriya': 'or',
    'punjabi': 'pa',
    'tamil': 'ta',
    'telugu': 'te',
    'kannada': 'kn',
    'nepali': 'ne',
    'urdu': 'ur',
    'goan': 'gom',
    'maithili': 'mai',
    'gujarati': 'gu',
    'malayalam': 'ml',
    'pali': 'pi',
    'santali': 'sat'
}

def get_supported_language_code(language):
    code = LANGUAGE_CODE_MAP.get(language.lower())
    if code in ['bh', 'pi', 'sat']:
        fallbacks = {'bh': 'hi', 'pi': 'sa', 'sat': 'bn'}
        logger.warning(f"{language} is not directly supported. Using {fallbacks[code]} as a fallback.")
        return fallbacks[code]
    return code or language.lower()

def chunk_text(text, max_length=1000): 
    """Split text into smaller chunks to avoid translation service limits."""
    if not text or len(text.strip()) == 0:
        return []
        
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1
        if current_length + word_length > max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
            
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def translate_with_mymemory(text, source_code, target_code):
    """Translate using MyMemory as a fallback."""
    try:
        translator = MyMemoryTranslator(source=source_code, target=target_code)
        return translator.translate(text)
    except Exception as e:
        logger.error(f"MyMemory translation failed: {str(e)}")
        raise

def translate_chunk(text, source_code, target_code, retries=3, delay=2):
    """Try multiple translation services with fallback."""
    if not text or len(text.strip()) == 0:
        return ""
        
    errors = []
    
    for attempt in range(retries):
        try:
            translator = GoogleTranslator(source=source_code, target=target_code)
            return translator.translate(text)
        except Exception as e:
            errors.append(f"Google Translate attempt {attempt + 1}: {str(e)}")
            time.sleep(delay * (attempt + 1))
    
    try:
        logger.info("Falling back to MyMemory translator")
        return translate_with_mymemory(text, source_code, target_code)
    except Exception as e:
        errors.append(f"MyMemory fallback: {str(e)}")
    
    error_msg = " | ".join(errors)
    raise Exception(f"All translation attempts failed: {error_msg}")

def translate_text(text_dict, source_language, target_language, retries=3, delay=2):
    """
    Translate text with multiple fallback services and improved error handling.
    """
    translated_dict = {}
    source_code = get_supported_language_code(source_language)
    target_code = get_supported_language_code(target_language)
    
    logger.info(f"Starting translation from {source_code} to {target_code}")
    
    for page, text in text_dict.items():
        if isinstance(text, bytes):
            text = text.decode('utf-8')
            
        logger.info(f"Processing page {page}")
        chunks = chunk_text(text)
        translated_chunks = []
        
        for i, chunk in enumerate(chunks):
            retry_count = 0
            success = False
            
            while not success and retry_count < retries:
                try:
                    logger.info(f"Translating chunk {i+1}/{len(chunks)} of page {page}")
                    translated_chunk = translate_chunk(
                        chunk, 
                        source_code, 
                        target_code, 
                        retries=retries, 
                        delay=delay
                    )
                    translated_chunks.append(translated_chunk)
                    success = True
                    logger.info(f"Successfully translated chunk {i+1}")
                except Exception as e:
                    retry_count += 1
                    logger.warning(f"Failed attempt {retry_count} for chunk {i+1}: {str(e)}")
                    if retry_count == retries:
                        translated_chunks.append(f"[Translation Error: {str(e)}]")
                
                if i < len(chunks) - 1:
                    time.sleep(delay)
        
        translated_dict[page] = ' '.join(translated_chunks)
        logger.info(f"Completed translation of page {page}")
    
    return translated_dict

if __name__ == "__main__":
    sample_text = {
        1: "Hello, how are you?",
        2: "This is a test translation."
    }
    source_lang = "english"
    target_lang = "hindi"
    
    try:
        translated = translate_text(sample_text, source_lang, target_lang)
        print(translated)
    except Exception as e:
        print(f"Translation failed: {str(e)}")