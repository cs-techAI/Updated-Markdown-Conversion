import streamlit as st
import markdown
from transformers import pipeline
from docx import Document
from PyPDF2 import PdfReader
import openai

# Function to convert .docx to text
def docx_to_text(docx_file):
    doc = Document(docx_file)
    text_content = ""
    for para in doc.paragraphs:
        text_content += para.text + "\n\n"
    return text_content.strip()

# Streamlit app setup
st.title("Markdown Conversion and LLM Interaction")

# Sidebar for user inputs
st.sidebar.header("User Input")
project_id = st.sidebar.text_input("Project ID", key="project_id_input")
location = st.sidebar.text_input("Location", key="location_input")

# Select Model Type: API Key or No API Key
model_type = st.sidebar.radio("Select Model Type", ["Without API Key", "With API Key"], key="model_type_select")

if model_type == "Without API Key":
    # Select Model without API Key (only facebook/bart)
    model_without_api_key = st.sidebar.selectbox("Select Model (without API Key)",
                                                   ["facebook/bart-large-cnn"],
                                                   key="model_without_api_key_select")
else:
    # Select Model with API Key options
    model_with_api_key = st.sidebar.selectbox("Select Model (with API Key)",
                                               ["OpenAI GPT-3", "Google Gemini", "T5", "GPT-2", "PEGASUS", "mT5"],
                                               key="model_with_api_key_select")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password", key="openai_api_key")

# Option to choose between file upload or text input
input_method = st.radio("Choose Input Method", ["Upload a File", "Enter Text"], key="input_method_select")

# File upload section if 'Upload a File' is selected
uploaded_file = None
if input_method == "Upload a File":
    uploaded_file = st.file_uploader("Choose a File", type=["txt", "pdf", "docx"], key="file_upload")

# Text area for direct input if 'Enter Text' is selected
text_input = ""
if input_method == "Enter Text":
    text_input = st.text_area("Paste your text here:", key="text_area_input")

# Load the Hugging Face model pipeline for summarization if selected
@st.cache_resource
def load_model(model_name):
    if model_name in ["facebook/bart-large-cnn", "T5", "GPT-2", "PEGASUS", "mT5"]:
        return pipeline("summarization", model=model_name)
    return None

# Process the input when the button is clicked
if st.button("Process"):
    file_content = ""

    if input_method == "Upload a File":
        if not uploaded_file:
            st.error("Error: No file uploaded!")
        else:
            with st.spinner("Processing File..."):
                file_extension = uploaded_file.name.split(".")[-1]
                if file_extension == "docx":
                    file_content = docx_to_text(uploaded_file)
                elif file_extension == "txt":
                    file_content = uploaded_file.read().decode("utf-8")
                elif file_extension == "pdf":
                    pdf_reader = PdfReader(uploaded_file)
                    file_content = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
                else:
                    st.error("Unsupported file type!")
                    st.stop()

    elif input_method == "Enter Text":
        if not text_input:
            st.error("Error: No text entered!")
            st.stop()
        else:
            file_content = text_input

    # Check for empty content
    if not file_content.strip():
        st.error("Error: The input text is empty!")
        st.stop()

    # Display original content
    st.subheader("Original Content:")
    st.text_area("Original Content:", file_content, height=200, key="original_content_area")

    # Convert to Markdown and display
    st.subheader("Markdown Content:")
    markdown_content = markdown.markdown(file_content)
    st.text_area("Markdown Converted Content:", markdown_content, height=200, key="markdown_content_area")

    # Check if the text is long enough for summarization and summarize accordingly
    try:
        if model_type == "Without API Key" and model_without_api_key == "facebook/bart-large-cnn":
            model_pipeline = load_model(model_without_api_key)
            response = model_pipeline(file_content, max_length=150, min_length=30, truncation=True)

            # Check if response contains expected data
            if response and len(response) > 0 and 'summary_text' in response[0]:
                summary_text = response[0]['summary_text']
                st.subheader(f"Summary from {model_without_api_key}:")
                st.write(summary_text)
            else:
                st.error("No summary available.")

        elif model_type == "With API Key" and model_with_api_key:
            if not openai_api_key and model_with_api_key == "OpenAI GPT-3":
                st.error("To use OpenAI GPT-3, please provide your OpenAI API Key.")
            else:
                openai.api_key = openai_api_key  # Set OpenAI API Key

                try:
                    if model_with_api_key == "OpenAI GPT-3":
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": file_content}],
                            max_tokens=150,
                        )
                        summary_text = response['choices'][0]['message']['content']
                        st.subheader(f"Summary from {model_with_api_key}:")
                        st.write(summary_text)

                    else:  # Placeholder for Google Gemini and other models requiring API keys.
                        response = openai.ChatCompletion.create(  # Replace this with actual Google Gemini API call.
                            model=model_with_api_key.lower(),
                            messages=[{"role": "user", "content": file_content}],
                            max_tokens=150,
                        )
                        summary_text = response['choices'][0]['message']['content']
                        st.subheader(f"Summary from {model_with_api_key}:")
                        st.write(summary_text)

                except Exception as e:
                    st.error(f"An error occurred while calling {model_with_api_key}: {e}")

    except Exception as e:
        st.error(f"An error occurred during summarization: {e}")
