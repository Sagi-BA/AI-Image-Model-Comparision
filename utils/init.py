import streamlit as st
import os

def initialize():
    st.set_page_config(layout="wide", page_title="📷 המרת תמונות לקובץ PDF", page_icon="📷")

    # Load external CSS
    css_file_path = os.path.join('utils', 'styles.css')
    with open(css_file_path, 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    custom_file_path = os.path.join('utils', 'custom.css')
    with open(custom_file_path, 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)        

    # Load external JavaScript
    js_file_path = os.path.join('utils', 'script.js')
    with open(js_file_path, 'r') as f:
        st.markdown(f'<script>{f.read()}</script>', unsafe_allow_html=True)

    # Load header and footer content
    header_file_path = os.path.join('utils', 'header.md')
    try:
        with open(header_file_path, 'r', encoding='utf-8') as header_file:
            header_content = header_file.read()
    except FileNotFoundError:
        st.error("header.md file not found in utils folder.")
        header_content = ""  # Provide a default empty header

    footer_file_path = os.path.join('utils', 'footer.md')
    try:
        with open(footer_file_path, 'r', encoding='utf-8') as footer_file:
            footer_content = footer_file.read()
    except FileNotFoundError:
        st.error("footer.md file not found in utils folder.")
        footer_content = ""  # Provide a default empty footer

    return header_content, footer_content