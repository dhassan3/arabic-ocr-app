import streamlit as st
from PIL import Image
import easyocr
from pdf2image import convert_from_bytes
import tempfile
import arabic_reshaper
from bidi.algorithm import get_display

st.set_page_config(page_title="Arabic OCR App", page_icon="🔍")
st.title("🇸🇦 Improved Arabic OCR App")
st.markdown("""
Upload images or PDFs with Arabic text for better extraction.  
Uses advanced deep-learning OCR – more accurate for connected letters and diacritics.
""")

# Initialize EasyOCR reader (Arabic + English for mixed text)
@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(['ar', 'en'], gpu=False)  # Set gpu=True if your deployment supports it

reader = get_ocr_reader()

uploaded_file = st.file_uploader("Upload image or PDF", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    if uploaded_file.type.startswith('image/'):
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", use_column_width=True)
        images = [img]
    else:
        st.info("PDF uploaded – processing pages...")
        with st.spinner("Converting PDF to images..."):
            images = convert_from_bytes(uploaded_file.getvalue(), dpi=300)

    if st.button("Extract Text"):
        with st.spinner("Running OCR (this may take a moment)..."):
            extracted_text = ""

            for idx, img in enumerate(images):
                # EasyOCR extraction
                result = reader.readtext(img, detail=0, paragraph=True)  # paragraph=True groups lines better
                
                page_text = "\n".join(result)
                
                # Fix RTL and shaping
                reshaped = arabic_reshaper.reshape(page_text)
                bidi_text = get_display(reshaped)
                
                extracted_text += f"--- Page {idx+1} ---\n{bidi_text}\n\n"

            st.success("Extraction complete!")
            st.text_area("Extracted Arabic Text", extracted_text, height=400)
            
            st.download_button(
                "📥 Download as TXT",
                extracted_text,
                file_name="arabic_ocr_text.txt",
                mime="text/plain"
            )

            st.info("💡 Tip: For best results, use high-resolution, clear images. EasyOCR handles complex Arabic better than basic engines!")

st.markdown("---")
st.caption("Upgraded with EasyOCR for superior Arabic accuracy ❤️")
