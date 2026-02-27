import streamlit as st
import base64
import os
# ---------- PAGE CONTENT ----------
st.title("📚 Sumber Pembelajaran")

#Menampilkan semua file pdf dalam bentuk embed dan gallery yang ada pada data/documents
def displayPDF(file_path):
    """Display a PDF file inside Streamlit."""
    if not os.path.exists(file_path):
        st.error(f"❌ File not found: {file_path}")
        return

    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")

    pdf_display = f"""
        <iframe 
            src="data:application/pdf;base64,{base64_pdf}" 
            width="100%" 
            height="800" 
            style="border:none;">
        </iframe>
    """
    st.components.v1.html(pdf_display, height=800, scrolling=True)

col1, col2 = st.columns(2)
with col1:
    st.header("Sumber Belajar 1")
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents", "clean_k13.pdf")
    displayPDF("data/documents/clean_k13.pdf")
with col2:
    st.header("Sumber Belajar 2")
    pdf_path_2 = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents", "clean_kmerdeka.pdf")
    displayPDF("data/documents/clean_kmerdeka.pdf")
# with col3:
#     st.header("Sumber Belajar 3")