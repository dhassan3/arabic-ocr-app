import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
import tempfile
from pathlib import Path
import arabic_reshaper
from bidi.algorithm import get_display
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt

st.set_page_config(page_title="Arabic Scanned PDF → Word (PaddleOCR)", page_icon="📄🔍")
st.title("🇸🇦 Scanned Arabic PDF/Image → Editable Word")
st.markdown("""
Upload scanned PDFs or images with Arabic text.  
Extracts text using PaddleOCR (high accuracy for Arabic) and creates an editable .docx with proper RTL formatting.
""")

# Cache PaddleOCR import and initialization to load only once (fixes "PDX initialized" error)
@st.cache_resource
def load_paddle_ocr():
    from paddleocr import PaddleOCR
    return PaddleOCR(use_angle_cls=True, lang='ar', use_gpu=False)

ocr = load_paddle_ocr()

uploaded_file = st.file_uploader(
    "Upload scanned PDF or image",
    type=["pdf", "jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()

    # Preview
    st.info(f"File uploaded: {uploaded_file.name}")
    if uploaded_file.type.startswith("image/"):
        img = Image.open(uploaded_file)
        st.image(img, caption="Preview", use_column_width=True)
        images = [img]
    else:
        with st.spinner("Converting PDF to images..."):
            images = convert_from_bytes(file_bytes, dpi=300)

    if st.button("Extract Text & Create Word File"):
        with st.spinner("Running Arabic OCR..."):
            doc = Document()
            doc.add_heading(f"Extracted from: {uploaded_file.name}", level=1)

            for page_num, img in enumerate(images, 1):
                # Save temp image
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    img.save(tmp.name, format="JPEG")
                    temp_path = tmp.name

                # OCR
                result = ocr.ocr(temp_path, cls=True)

                page_lines = []
                for line in result[0] if result else []:
                    text = line[1][0]
                    page_lines.append(text)

                page_text = "\n".join(page_lines).strip()

                if page_text:
                    # Fix shaping & RTL
                    reshaped = arabic_reshaper.reshape(page_text)
                    bidi_text = get_display(reshaped)

                    # Add to Word
                    p = doc.add_paragraph(bidi_text)
                    p.paragraph_format.right_to_left = True
                    p.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                    p.paragraph_format.line_spacing = 1.15

                    for run in p.runs:
                        run.font.size = Pt(12)
                        # Arabic font fallback
                        for font_name in ['Arabic Typesetting', 'Traditional Arabic', 'Simplified Arabic', 'Sakkal Majalla', 'Arial']:
                            run.font.name = font_name
                            break

                doc.add_page_break()

            # Save Word
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
                doc.save(tmp_docx.name)
                docx_path = tmp_docx.name

        st.success("Done! Download your editable Word file.")

        # Download
        with open(docx_path, "rb") as f:
            st.download_button(
                label="📥 Download Word (.docx)",
                data=f,
                file_name=f"arabic_ocr_{uploaded_file.name.rsplit('.', 1)[0]}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        # Preview text
        with st.expander("View extracted text"):
            st.text_area("Raw text", page_text if 'page_text' in locals() else "No text found", height=200)

        st.info("Tip: In Word, use Ctrl+Right Shift for RTL if needed. PaddleOCR works best on clear scans.")

st.markdown("---")
st.caption("Powered by PaddleOCR – accurate Arabic extraction ❤️")
