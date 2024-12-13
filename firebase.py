import firebase_admin
from firebase_admin import credentials, auth, firestore
import streamlit as st
import os

def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate('D:\mega project gemini\mega-project-gemini-46ed099384d9.json')
            firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        st.error(f"Firebase initialization error: {e}")
        return False

def signup(email, password, name):
    """Create a new user account and store in Firestore"""
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        
        db = firestore.client()
        
        users_ref = db.collection('user')
        users_ref.document(user.uid).set({
            'name': name,
            'email': email,
            'created_at': firestore.SERVER_TIMESTAMP,
            'last_login': firestore.SERVER_TIMESTAMP,
            'password': password
        })
        
        return user
    except Exception as e:
        st.error(f"Signup error: {str(e)}")
        return None

def login(email, password):
    """Authenticate user and update last login"""
    try:
        user = auth.get_user_by_email(email)
        
        db = firestore.client()
        users_ref = db.collection('user').document(user.uid)
        users_ref.update({
            'last_login': firestore.SERVER_TIMESTAMP
        })
        
        return user
    except ValueError as e:
        st.error(f"Login error: {str(e)}")
        return None

def reset_password(email):
    """Send password reset email"""
    try:
        reset_link = auth.generate_password_reset_link(email)
        return reset_link
    except Exception as e:
        st.error(f"Password reset error: {str(e)}")
        return None

def get_user_info():
    """Get current logged-in user's information from Firestore"""
    try:
        if 'user' in st.session_state and st.session_state.user:
            db = firestore.client()
            user_doc = db.collection('user').document(st.session_state.user.uid).get()
            return user_doc.to_dict() if user_doc.exists else None
        return None
    except Exception as e:
        st.error(f"Error retrieving user info: {str(e)}")
        return None