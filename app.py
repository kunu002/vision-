# app.py
import streamlit as st
import os
import tempfile
from text_extraction import extract_text, LANGUAGE_MAP
from embedding import embed_text, model  
from translation import translate_text
from database import document_store
from qa_module import get_answer, get_language_error_message
from utils import save_to_zip
import firebase
import signup

IMAGES_DIR = 'images'
MAKERS_IMAGES = {
    'maker1': os.path.join(IMAGES_DIR, 'PhotoKunu.jpg'),
    'maker2': os.path.join(IMAGES_DIR, 'Sanuphoto.jpg'),
    'maker3': os.path.join(IMAGES_DIR, 'Rutujaphoto.jpg'),
    'maker4': os.path.join(IMAGES_DIR, 'Vinayakphoto.jpg'),
    'mentor': os.path.join(IMAGES_DIR, 'mentor.jpg')
}

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'text_dict' not in st.session_state:
        st.session_state.text_dict = None
    if 'input_language' not in st.session_state:
        st.session_state.input_language = None
    if 'translation_language' not in st.session_state:
        st.session_state.translation_language = None
    if 'embeddings_created' not in st.session_state:
        st.session_state.embeddings_created = False
    if 'page' not in st.session_state:
        st.session_state.page = "Home"
    if 'model_loaded' not in st.session_state:
        st.session_state.model_loaded = False
    if 'document_processed' not in st.session_state:
        st.session_state.document_processed = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def load_model():
    """Check if the model is loaded and set the flag"""
    if not st.session_state.model_loaded:
        try:
            if model:
                st.session_state.model_loaded = True
                return True
        except Exception as e:
            st.error(get_language_error_message('English', 'model_load'))
            return False
    return True

def create_embeddings():
    """Create embeddings from the text and store in database"""
    if not st.session_state.text_dict:
        return False
        
    if not st.session_state.embeddings_created:
        try:
            if not load_model():
                return False
                
            with st.spinner('Creating embeddings for Q&A... This may take a moment.'):
                progress_bar = st.progress(0)
                
                lang = st.session_state.input_language or 'English'
                
                embedded_text = embed_text(st.session_state.text_dict, lang)
                progress_bar.progress(100)
                
                document_store.add_to_database(embedded_text)
                
                st.session_state.embeddings_created = True
                return True
                
        except Exception as e:
            error_msg = get_language_error_message('English', 'embedding')
            st.error(f"{error_msg}: {str(e)}")
            return False
            
    return True

def reset_session():
    st.session_state.embeddings_created = False
    st.session_state.document_processed = False
    st.session_state.translation_language = None
    global document_store
    document_store = document_store.__class__()

def home():
    st.title('Veda VisionGPT')
    st.write("Welcome to Veda VisionGPT. Upload a document to get started.")

    languages = list(LANGUAGE_MAP.keys())
    
    selected_input_language = st.selectbox('Select input language', languages)

    uploaded_file = st.file_uploader("Choose a document (PDF, Image, or DOCX)", type=['pdf', 'docx' , 'png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        if st.button('Process Document'):
            reset_session()
            
            with st.spinner('Extracting text from document...'):
                try:
                    text_dict = extract_text(uploaded_file, selected_input_language)

                    if isinstance(text_dict, dict) and all(isinstance(value, str) and value.startswith("Error processing") for value in text_dict.values()):
                        st.error(f"Failed to extract text from the document: {list(text_dict.values())[0]}")
                    else:
                        st.session_state.text_dict = text_dict
                        st.session_state.input_language = selected_input_language
                        st.session_state.document_processed = True
                        
                        if 'selected_page' not in st.session_state:
                            st.session_state.selected_page = 1

                        st.session_state.zip_content = save_to_zip(text_dict)
                        st.success("Text extraction completed!")

                finally: 
                    pass

    if hasattr(st.session_state, 'zip_content') and st.session_state.zip_content:
        st.download_button(
            label="Download extracted text",
            data=st.session_state.zip_content,
            file_name="extracted_text.zip",
            mime="application/zip"
        )

    if st.session_state.get('document_processed', False):
        total_pages = len(st.session_state.text_dict)
        
        st.header("Extracted Document Pages")
        
        page_selector_key = f"page_selector_{hash(tuple(st.session_state.text_dict.keys()))}"
        
        selected_page = st.selectbox(
            'Select Page', 
            list(range(1, total_pages + 1)), 
            index=st.session_state.selected_page - 1,
            key=page_selector_key
        )
        
        st.session_state.selected_page = selected_page
        
        st.subheader(f"Page {selected_page}")
        st.text_area(
            "Page Content", 
            value=st.session_state.text_dict[selected_page], 
            height=300, 
            disabled=True
        )

        st.write("You can now:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Translate Text"):
                st.session_state.page = "Translate"
                st.experimental_rerun()
        with col2:
            if st.button("Ask Questions"):
                st.session_state.page = "Q&A"
                st.experimental_rerun()

def translate():
    st.title("Translation")
    if not st.session_state.document_processed:
        st.warning("Please process a document first.")
        if st.button("Go to Home"):
            st.session_state.page = "Home"
            st.experimental_rerun()
        return

    languages = list(LANGUAGE_MAP.keys())
    
    target_language = st.selectbox('Select target language', languages)
    if st.button('Translate'):
        with st.spinner('Translating...'):
            try:
                translated_text = translate_text(
                    st.session_state.text_dict, 
                    st.session_state.input_language, 
                    target_language
                )
                if translated_text:
                    st.session_state.translation_language = target_language
                    st.session_state.translated_text = translated_text
                    
                    st.session_state.translated_zip_content = save_to_zip(translated_text)
                    st.success("Translation completed!")
                    
                    st.session_state.selected_page = 1
                else:
                    st.error("Translation failed. Please try again.")
            except Exception as e:
                st.error(get_language_error_message('English', 'translation'))

    if hasattr(st.session_state, 'translated_zip_content') and st.session_state.translated_zip_content:
        st.download_button(
            label="Download translated text",
            data=st.session_state.translated_zip_content,
            file_name="translated_text.zip",
            mime="application/zip"
        )


    if hasattr(st.session_state, 'translated_text') and st.session_state.translated_text:
        total_pages = len(st.session_state.translated_text)
        
        st.header("Translated Document Pages")
        
        selected_page = st.selectbox(
            'Select Page', 
            list(range(1, total_pages + 1)), 
            index=st.session_state.selected_page - 1
        )
        
        st.session_state.selected_page = selected_page
        
        st.subheader(f"Page {selected_page}")
        st.text_area(
            "Page Content", 
            value=st.session_state.translated_text[selected_page], 
            height=300, 
            disabled=True
        )

    if st.button("Back to Home"):
        st.session_state.page = "Home"
        st.experimental_rerun()
        st.experimental_rerun()

def qa():
    st.title("Ask Questions")
    if not st.session_state.document_processed:
        st.warning("Please process a document first.")
        if st.button("Go to Home"):
            st.session_state.page = "Home"
            st.experimental_rerun()
        return

    if not st.session_state.embeddings_created:
        st.info("Preparing document for Q&A... This may take a moment.")
        success = create_embeddings()
        if not success:
            st.error("Failed to prepare document for Q&A. Please try again.")
            return
        st.success("Document prepared for Q&A!")

    chat_container = st.container()
    
    with chat_container:
        for q, a in st.session_state.chat_history:
            st.write("Question:", q)
            st.write("Answer:", a)
            st.write("---")

    user_question = st.text_input("Enter your question about the document:")
    
    if user_question:
        if st.button('Get Answer'):
            with st.spinner('Searching for answer...'):
                try:
                    answer = get_answer(
                        user_question, 
                        st.session_state.input_language, 
                        st.session_state.translation_language
                    )
                    st.session_state.chat_history.append((user_question, answer))
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"An error occurred while generating the answer: {str(e)}")

    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.experimental_rerun()

    if st.button("Back to Home"):
        st.session_state.page = "Home"
        st.experimental_rerun()

def about():
    st.title("Veda VisionGPT: Bridging Language Barriers")
    
    st.write("""
    Veda VisionGPT is an advanced document processing and analysis tool 
    that combines Optical Character Recognition (OCR), machine translation, 
    and AI-powered question answering to provide a comprehensive solution 
    for multilingual document understanding.
    """)
    
    st.header("Key Features")
    features = [
        "Text Extraction from PDFs , Docs and Images",
        "Support for multiple Indian Languages",
        "Advanced Translation Capabilities",
        "AI-Powered Contextual Question Answering"
    ]
    for feature in features:
        st.write(f"- {feature}")
    
    st.header("Our Team")
    
    cols = st.columns(4)
    
    makers = [
        {
            'name': 'Kunal Sapkal',
            'role': 'Machine Learning Engineer',
            'image': MAKERS_IMAGES['maker1']
        },
        {
            'name': 'Sanika Kadam', 
            'role': 'Backend Developer',
            'image': MAKERS_IMAGES['maker2']
        },
        {
            'name': 'Rutuja Mulik',
            'role': 'Data Analyst',
            'image': MAKERS_IMAGES['maker3']
        },
        {
            'name': 'Vinayak Gharge',
            'role': 'System Architect',
            'image': MAKERS_IMAGES['maker4']
        }
    ]
    
    for i, maker in enumerate(makers):
        with cols[i]:
            try:
                st.image(maker['image'], width=100, use_column_width=False)
            except Exception as e:
                st.write(f"Image not found: {e}")
            st.write(f"**{maker['name']}**")
            st.write(maker['role'])
    
    st.header("Thanks To:")
    mentor_col = st.columns(3)[1] 
    with mentor_col:
        try:
            st.image(MAKERS_IMAGES['mentor'], width=250)
        except Exception as e:
            st.write(f"Mentor image not found: {e}")
        st.write("**Dr. Mentor Name**")
        st.write("Senior Research Advisor")


def logout():
    """Handle user logout and clean up session"""
    keys_to_clear = [
        'text_dict', 
        'input_language', 
        'translation_language', 
        'embeddings_created', 
        'document_processed', 
        'chat_history', 
        'translated_text',
        'zip_content',
        'translated_zip_content',
        'user',
        'logged_in'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    try:
        global document_store
        document_store = document_store.__class__()
    except Exception as e:
        st.error(f"Error clearing vector database: {e}")
    
    st.experimental_rerun()
    


def main():
    st.markdown("""
    <style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #201F1FFF;
    }
    
    /* Navigation menu styling */
    .stRadio > div {
        display: flex;
        flex-direction: column;
    }
    
    /* Radio button styling */
    div[role="radiogroup"] > label {
        font-size: 28px !important;
        font-weight: bold !important;
        color: #333 !important;
        margin-bottom: 10px !important;
        padding: 10px 15px !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    /* Hover effect */
    div[role="radiogroup"] > label:hover {
        background-color: #117474FF !important;
        transform: scale(1.05) !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        cursor: pointer !important;
    }
    
    /* Selected option styling */
    div[role="radiogroup"] > label[data-selected="true"] {
        background-color: #2C9AE3FF !important;
        color: white !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }
    
    /* Welcoming user styling */
    [data-testid="stSidebarUserContent"] {
        font-size: 20 px !important;
        font-weight: bold !important;
        color: #F7F9FAFF !important;
        margin-bottom: 15px !important;
    }
    
    /* Logout button styling */
    .stButton > button {
        background-color: #CF2424FF !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #c0392b !important;
        transform: scale(1.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    initialize_session_state()

    if not hasattr(st.session_state, 'logged_in') or not st.session_state.logged_in:
        signup.main()
        return

    st.sidebar.title("Navigation")
    pages = {
        "About": about,
        "Home": home,
        "Translate": translate,
        "Q&A": qa
    }

    st.session_state.page = st.sidebar.radio("Go to", list(pages.keys()), key="page_selector")

    if hasattr(st.session_state, 'user'):
        user_info = firebase.get_user_info()
        if user_info:
            st.sidebar.write(f"Welcome, {user_info.get('name', 'User')}")

    st.sidebar.markdown("---") 
    if st.sidebar.button("Logout"):
        logout()

    if st.session_state.page == "Q&A" and not st.session_state.model_loaded:
        with st.spinner("Loading Q&A model..."):
            load_model()

    pages[st.session_state.page]()

if __name__ == '__main__':
    main()