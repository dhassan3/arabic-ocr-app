import streamlit as st
from paddleocr import PaddleOCR
from PIL import Image
from pdf2image import convert_from_bytes
import tempfile
import arabic_reshaper
from bidi.algorithm import get_display

st.set_page_config(page_title="Advanced Arabic OCR with PaddleOCR", page_icon="🔍")
st.title("🇸🇦 Advanced Arabic OCR App (PaddleOCR)")
st.markdown("""
Upload images or PDFs with Arabic text for **high-accuracy** extraction.  
PaddleOCR excels at connected letters, diacritics, and complex fonts.
""")

# Initialize PaddleOCR with Arabic model (downloads on first run)
@st.cache_resource
def get_ocr_model():
    # 'ar' uses Arabic-optimized models; models auto-download
    return PaddleOCR(use_angle_cls=True, lang='ar', use_gpu=False)  # Set use_gpu=True if available

ocr = get_ocr_model()

uploaded_file = st.file_uploader("Upload image (JPG/PNG) or PDF", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file:
    file_bytes = uploaded_file.getvalue()

    # Preview
    if uploaded_file.type.startswith("image/"):
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", use_column_width=True)
        images = [img]
    else:
        st.info("PDF uploaded – converting pages to images...")
        with st.spinner("Converting PDF..."):
            images = convert_from_bytes(file_bytes, dpi=300)

    if st.button("Extract Arabic Text"):
        with st.spinner("Running PaddleOCR (this may take a moment)..."):
            extracted_text = ""

            for idx, img in enumerate(images):
                # Save temp image for PaddleOCR
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    img.save(tmp.name, format="JPEG")
                    temp_path = tmp.name

                # OCR
                result = ocr.ocr(temp_path, cls=True)  # cls=True for angle classification

                page_lines = []
                for line in result[0]:  # result[0] for single image
                    text = line[1][0]  # Text content
                    page_lines.append(text)

                page_text = "\n".join(page_lines)

                # Fix RTL shaping and direction
                reshaped = arabic_reshaper.reshape(page_text)
                bidi_text = get_display(reshaped)

                extracted_text += f"--- Page {idx+1} ---\n{bidi_text}\n\n"

            st.success("Extraction complete!")
            st.text_area("Extracted Arabic Text", extracted_text, height=400)

            st.download_button(
                label="📥 Download as TXT",
                data=extracted_text,
                file_name="arabic_ocr_paddle.txt",
                mime="text/plain"
            )

            st.info("💡 Tip: PaddleOCR is state-of-the-art for Arabic. For best results: high-res, clear scans.")

st.markdown("---")
st.caption("Powered by PaddleOCR – superior Arabic accuracy ❤️")
