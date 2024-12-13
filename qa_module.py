# qa_module.py
import google.generativeai as genai
from embedding import embed_text, model as embedding_model
from database import document_store
import os
from dotenv import load_dotenv
from langdetect import detect, LangDetectException
import sys
from text_extraction import LANGUAGE_MAP

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel('gemini-pro')

def detect_language(text: str) -> str:
    """
    Detect the language of the text
    Returns language name or 'English' if detection fails
    """
    try:
        detected_code = detect(text)
        for lang, code in LANGUAGE_MAP.items():
            if code == detected_code:
                return lang
        return 'English'
    except LangDetectException:
        return 'English'

def get_supported_languages(input_language: str, translation_language: str = None) -> list:
    """
    Get a list of supported languages including input, translated, and English
    """
    supported_languages = ['English']
    if input_language and input_language not in supported_languages:
        supported_languages.append(input_language)
    if translation_language and translation_language not in supported_languages:
        supported_languages.append(translation_language)
    return supported_languages

def get_answer(question: str, input_language: str = None, translation_language: str = None) -> str:
    try:
        question_language = detect_language(question)
        
        supported_languages = get_supported_languages(input_language, translation_language)
        
        if question_language not in supported_languages:
            question_language = 'English'
        
        question_embedding = embedding_model.encode(question, normalize_embeddings=True)
        
        relevant_chunks = document_store.search_database(question_embedding, k=5)  
        
        if not relevant_chunks:
            return get_language_error_message(question_language, 'no_results')
        
        context = "\n\n".join([chunk['text'] for chunk in relevant_chunks])
        
        chunk_languages = [chunk['language'] for chunk in relevant_chunks]
        predominant_language = max(set(chunk_languages), key=chunk_languages.count)
        
        prompt = f"""You are an expert multilingual assistant.
        Answer the following question based on the provided context.
        
        Important instructions:
        1. The question is in {question_language}
        2. The context is predominantly in {predominant_language}
        3. Provide the answer ONLY in {question_language}
        4. If you cannot find the answer in the context, say so in {question_language}
        5. Maintain formal and respectful language
        6. If technical terms appear in English, you may keep them in English
        
        Context:
        {context}
        
        Question: {question}
        
        Answer in {question_language}:"""
        
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text.strip()
        else:
            return get_language_error_message(question_language, 'no_answer')
            
    except Exception as e:
        print(f"Error in get_answer: {str(e)}", file=sys.stderr)
        return get_language_error_message(question_language, 'general_error')

def get_language_error_message(language: str, error_type: str) -> str:

    messages = {
        'Marathi': {
            'no_results': 'माफ करा, या प्रश्नासंबंधी कोणतेही उपयुक्त संदर्भ मिळाले नाहीत.',
            'no_answer': 'माफ करा, या प्रश्नाचे उत्तर देण्यासाठी प्रासंगिक माहिती सापडली नाही.',
            'general_error': 'त्रुटी आली: {}'
        },
        'Hindi': {
            'no_results': 'क्षमा करें, इस प्रश्न के लिए कोई प्रासंगिक संदर्भ नहीं मिला।',
            'no_answer': 'क्षमा करें, इस प्रश्न का उत्तर देने के लिए प्रासंगिक जानकारी नहीं मिली।',
            'general_error': 'त्रुटि आई: {}'
        },
        'English': {
            'no_results': 'I\'m sorry, I could not find any relevant context to answer your question.',
            'no_answer': 'I apologize, I could not find any information to provide an answer to your question.',
            'general_error': 'An error occurred: {}'
        }
    }
    
    return messages.get(language, {}).get(error_type, f"Error during {error_type}")