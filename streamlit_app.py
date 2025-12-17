import streamlit as st
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import tempfile
from pathlib import Path
import arabic_reshaper
from bidi.algorithm import get_display

st.set_page_config(page_title="Arabic OCR App", page_icon="🔍")
st.title("🇸🇦 Arabic OCR App")
st.markdown("""
Upload an image or PDF with Arabic text, and extract editable text instantly.  
Supports right-to-left (RTL) text, connected letters, and scanned documents.
""")

# File uploader
uploaded_file = st.file_uploader("Choose an image or PDF", type=["jpg", "png", "pdf"], accept_multiple_files=False)

if uploaded_file is not None:
    # Preview the upload
    if uploaded_file.type in ["image/jpeg", "image/png"]:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", use_column_width=True)
    else:
        st.info("PDF uploaded. OCR will process each page.")

    if st.button("Extract Arabic Text"):
        with st.spinner("Performing OCR..."):
            extracted_text = ""

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                if uploaded_file.type == "application/pdf":
                    # Convert PDF to images
                    pdf_path = temp_path / uploaded_file.name
                    with open(pdf_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    images = convert_from_path(str(pdf_path))
                else:
                    # Single image
                    images = [Image.open(uploaded_file)]

                # OCR each image/page
                for idx, img in enumerate(images):
                    # Perform OCR with Arabic language
                    text = pytesseract.image_to_string(img, lang='ara')
                    
                    # Reshape and apply bidi for proper RTL display
                    reshaped = arabic_reshaper.reshape(text)
                    bidi_text = get_display(reshaped)
                    
                    extracted_text += f"--- Page {idx+1} ---\n{bidi_text}\n\n"

            # Display results
            st.success("Extraction complete!")
            st.text_area("Extracted Arabic Text", extracted_text, height=300)

            # Download option
            st.download_button(
                label="📥 Download as TXT",
                data=extracted_text,
                file_name="extracted_arabic_text.txt",
                mime="text/plain"
            )

else:
    st.info("👆 Upload a file to begin.")

st.markdown("---")
st.caption("Made with ❤️ for accurate Arabic text extraction")
