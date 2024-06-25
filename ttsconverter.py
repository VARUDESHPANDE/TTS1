import streamlit as st
from docx import Document
from gtts import gTTS
import os
import shutil
import openai

# Ensure necessary directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('output', exist_ok=True)

# Extract OpenAI API key from environment variable
openai_api_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = openai_api_key

def extract_text_from_docx(docx_file):
    doc = Document(docx_file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def convert_text_to_speech(text, output_path):
    try:
        tts = gTTS(text)
        tts.save(output_path)
    except Exception as e:
        return str(e)
    return None

def clear_directory(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)

def latex_to_readable(latex_code):
    combined_prompt = f"""
    You are an intelligent assistant. Your task is to convert LaTeX code in the given text to plain English and provide summaries for tables and images. Follow these specific instructions:

    1. Keep the plain text exactly as it is. Do not provide any overview or summary of the entire text.
    2. Convert any LaTeX code into a human-readable format. For example, $\\alpha$ should be read as "alpha", and $ax^2+bx+c=0$ should be read as "a x squared plus b x plus c equals zero".
    3. For tables, provide a summarized explanation of the concept covered in the table without mentioning the formatting. For example, if a table shows a logical representation of inputs and outputs, explain the logical relationship in plain English.
    4. For images, mention that there is an image at that position, but do not narrate the source or provide additional context about the image.

    Text to convert:
    {latex_code}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an intelligent assistant."},
                {"role": "user", "content": combined_prompt}
            ]
        )
        human_readable_text = response.choices[0].message['content'].strip()
    except Exception as e:
        return f"Error: {e}"
    
    return human_readable_text

# Streamlit app
st.title("LaTeX to Speech Converter")

st.write("""Upload a DOCX file with LaTeX content, and get an MP3 narration.""")

uploaded_file = st.file_uploader("Choose a DOCX file", type="docx")

if uploaded_file is not None:
    clear_directory('uploads')
    clear_directory('output')
    
    # Save uploaded file
    file_path = os.path.join('uploads', uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    text = extract_text_from_docx(file_path)

    # Use ChatGPT Turbo to convert text
    try:
        with st.spinner("Converting LaTeX to human-readable text..."):
            converted_text = latex_to_readable(text)
        st.success("Conversion successful!")
    except Exception as e:
        st.error(f"Error communicating with OpenAI: {e}")

    st.write("### Converted Text")
    st.write(converted_text)

    mp3_output_path = os.path.join('output', 'final.mp3')
    error = convert_text_to_speech(converted_text, mp3_output_path)
    if error:
        st.error(f"Error during text-to-speech conversion: {error}")
    else:
        if os.path.exists(mp3_output_path):
            st.success("Text-to-speech conversion completed and MP3 file created!")
            st.write("Download your MP3 file:")
            with open(mp3_output_path, "rb") as f:
                st.download_button(
                    label="Download MP3",
                    data=f,
                    file_name="final.mp3",
                    mime="audio/mpeg"
                )
        else:
            st.error("Text-to-speech conversion failed: MP3 file not created.")
