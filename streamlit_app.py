import streamlit as st
from paddleocr import PaddleOCR
from PIL import Image
from pdf2image import convert_from_bytes
import tempfile
from pathlib import Path
import arabic_reshaper
from bidi.algorithm import get_display
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt

st.set_page_config(page_title="Arabic Scanned PDF → Editable Word (PaddleOCR)", page_icon="📄🔍")
st.title("🇸🇦 Scanned Arabic PDF/Image → Editable Word")
st.markdown("""
Upload scanned/image-based PDFs or images with Arabic text.  
This app uses **PaddleOCR** (state-of-the-art for Arabic) to extract text and create a clean, editable .docx file with proper RTL formatting.
""")

# Cache PaddleOCR model (downloads on first run)
@st.cache_resource
def load_paddle_ocr():
    return PaddleOCR(use_angle_cls=True, lang='ar', use_gpu=False)  # 'ar' for Arabic-optimized model

ocr = load_paddle_ocr()

uploaded_file = st.file_uploader(
    "Upload scanned PDF or image (JPG/PNG)",
    type=["pdf", "jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    # Preview
    st.info(f"File uploaded: {uploaded_file.name}")
    if uploaded_file.type.startswith("image/"):
        img = Image.open(uploaded_file)
        st.image(img, caption="Preview", use_column_width=True)
        images = [img]
    else:
        with st.spinner("Converting PDF pages to images..."):
            images = convert_from_bytes(uploaded_file.getvalue(), dpi=300)

    if st.button("Extract Arabic Text & Create Word File"):
        with st.spinner("Running high-accuracy Arabic OCR..."):
            doc = Document()
            doc.add_heading(f"Extracted from: {uploaded_file.name}", level=1)

            for page_num, img in enumerate(images, 1):
                # Save temp image for PaddleOCR
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    img.save(tmp.name, format="JPEG")
                    temp_path = tmp.name

                # OCR
                result = ocr.ocr(temp_path, cls=True)

                page_lines = []
                for line in result[0] if result else []:
                    text = line[1][0]  # Extract text
                    page_lines.append(text)

                page_text = "\n".join(page_lines).strip()

                if page_text:
                    # Fix Arabic shaping & RTL order
                    reshaped = arabic_reshaper.reshape(page_text)
                    bidi_text = get_display(reshaped)

                    # Add to Word with RTL formatting
                    p = doc.add_paragraph(bidi_text)
                    p.paragraph_format.right_to_left = True
                    p.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                    p.paragraph_format.line_spacing = 1.15  # Better spacing for Arabic

                    for run in p.runs:
                        run.font.size = Pt(12)
                        # Fallback to best Arabic fonts
                        for font_name in ['Arabic Typesetting', 'Traditional Arabic', 'Simplified Arabic', 'Sakkal Majalla', 'Arial']:
                            run.font.name = font_name
                            break

                doc.add_page_break()  # Separate pages

            # Save Word file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
                doc.save(tmp_docx.name)
                docx_path = tmp_docx.name

        st.success("OCR complete! Arabic text extracted and formatted.")

        # Download Word
        with open(docx_path, "rb") as f:
            st.download_button(
                label="📥 Download Editable Word (.docx)",
                data=f,
                file_name=f"arabic_ocr_{uploaded_file.name.rsplit('.', 1)[0]}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        # Optional: Show raw text preview
        with st.expander("View extracted text preview"):
            st.text_area("Raw extracted text", page_text if 'page_text' in locals() else "No text found", height=200)

        st.info(
            "💡 Tip: Open the .docx in Microsoft Word and adjust font/line spacing if needed. "
            "PaddleOCR provides very good accuracy for printed Arabic — for best results use high-resolution scans."
        )

st.markdown("---")
st.caption("Powered by PaddleOCR – best-in-class Arabic OCR in 2025 ❤️")
