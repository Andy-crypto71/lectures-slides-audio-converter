import streamlit as st
import asyncio
import io
import os
import re
from pptx import Presentation
from docx import Document
from pypdf import PdfReader
import edge_tts


# --- TEXT CLEANING LOGIC ---

def clean_text(text):
    # Remove square brackets and content inside
    text = re.sub(r'\[.*?\]', '', text)

    # Remove curly braces and content inside
    text = re.sub(r'\{.*?\}', '', text)

    # Remove annoying symbols
    symbols_to_remove = ['[', ']', '{', '}', '/', '\\', '_', '*', '#']

    for symbol in symbols_to_remove:
        text = text.replace(symbol, ' ')

    # Clean extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


# --- FILE TEXT EXTRACTION ---

def extract_text(uploaded_file, ext):

    file_bytes = io.BytesIO(uploaded_file.read())

    if ext == "pptx":

        prs = Presentation(file_bytes)

        content = []

        for i, slide in enumerate(prs.slides):

            slide_text = []

            for shape in slide.shapes:

                if hasattr(shape, "text"):
                    slide_text.append(shape.text)

            content.append(f"Slide {i + 1}. " + " ".join(slide_text))

    elif ext == "docx":

        doc = Document(file_bytes)

        content = [p.text for p in doc.paragraphs if p.text.strip()]

    elif ext == "pdf":

        reader = PdfReader(file_bytes)

        content = []

        for i, page in enumerate(reader.pages):

            text = page.extract_text()

            if text:
                content.append(f"Page {i + 1}. {text}")

    else:
        return ""

    return " ... ".join(content)


# --- AUDIO GENERATION ---

async def save_audio(text, voice):

    communicate = edge_tts.Communicate(text, voice)

    await communicate.save("temp_output.mp3")

    return "temp_output.mp3"


# --- STREAMLIT UI ---

st.set_page_config(
    page_title="Study Audio Converter",
    page_icon="🎙️"
)

st.title("🎙️ Study Audio Converter")

st.write(
    "Convert your lecture slides and notes into audio instantly."
)

# Voice Selection
voice = st.selectbox(
    "Select Voice",
    [
        "en-GB-ThomasNeural",
        "en-US-GuyNeural",
        "en-US-AriaNeural"
    ]
)

# File Upload
file = st.file_uploader(
    "Upload PPTX, DOCX, or PDF",
    type=["pptx", "docx", "pdf"]
)

# Convert Button
if file and st.button("Convert to Audio"):

    file_extension = file.name.split(".")[-1].lower()

    with st.spinner("Reading and cleaning text..."):

        raw_text = extract_text(file, file_extension)

        if raw_text:

            final_text = clean_text(raw_text)

            with st.spinner("Generating audio..."):

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                audio_file = loop.run_until_complete(
                    save_audio(final_text, voice)
                )

                st.success("Audio generated successfully!")

                st.audio(audio_file)

                with open(audio_file, "rb") as f:

                    st.download_button(
                        label="Download MP3",
                        data=f,
                        file_name=f"{os.path.splitext(file.name)[0]}.mp3",
                        mime="audio/mpeg"
                    )

                # Cleanup
                if os.path.exists(audio_file):
                    os.remove(audio_file)

        else:
            st.error("No readable text found in the uploaded file.")