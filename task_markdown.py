import streamlit as st
import openai
import markdown
import google.generativeai as genai
from transformers import pipeline
from PyPDF2 import PdfReader
from docx import Document

st.set_page_config(page_title="Markitdown Lib")

st.title("Markdown Conversion")


project_id = st.sidebar.text_input("Enter Project ID", type="default")
location = st.sidebar.text_input("Enter Location", type="default")


if "file_content" not in st.session_state:        # uses session state to store the api key llm type,etc
    st.session_state.file_content = ""
if "markdown_content" not in st.session_state:
    st.session_state.markdown_content = ""
if "llm_option" not in st.session_state:
    st.session_state.llm_option = "Select LLM"
if "api_key" not in st.session_state:
    st.session_state.api_key = ""


uploaded_file = st.file_uploader("Choose a File", type=["txt", "pdf", "docx"])


if uploaded_file:
    if st.button("Convert File"):
        file_extension = uploaded_file.name.split(".")[-1]
        if file_extension == "txt":
            st.session_state.file_content = uploaded_file.read().decode("utf-8")

        elif file_extension == "pdf":
            pdf_reader = PdfReader(uploaded_file)
            file_content = ""
            for page in pdf_reader.pages:         # in thsi converted all the variables like file content to session state
                text = page.extract_text()
                if text:
                    file_content += text
            st.session_state.file_content = file_content


        elif file_extension == "docx":
            doc = Document(uploaded_file)
            file_content = ""
            for paragraph in doc.paragraphs:
                file_content += paragraph.text
            st.session_state.file_content = file_content

        else:
            st.error("Unsupported file type!")
            st.stop()


if st.session_state.file_content:
    st.subheader("Original Content:")
    st.text_area("Original File Content:", st.session_state.file_content, height=200)

    if st.session_state.markdown_content == "":       # session state applies here
        st.session_state.markdown_content = markdown.markdown(st.session_state.file_content)

    st.subheader("Markdown Content:")
    st.text_area("Markdown Converted Content:", st.session_state.markdown_content, height=200)

    
    llm_options = ["Select LLM", "OpenAI (GPT)", "Gemini", "Meta AI (LLaMA)"]
    st.session_state.llm_option = st.selectbox(
        "Select any LLM:",                         # here given select llm as default so the if loops works
        llm_options,                               # only when this option is not in default
        index=llm_options.index(st.session_state.llm_option) 
        if st.session_state.llm_option in llm_options else 0
    )

    
    if st.session_state.llm_option != "Select LLM":     
        st.session_state.api_key = st.text_input(          # requests only the required api key after choosing the llm 
            f"Enter your API Key for {st.session_state.llm_option}",   
            type="password", 
            value=st.session_state.api_key    # initializing the value vari
        )

    
    if st.session_state.api_key and st.session_state.llm_option != "Select LLM":

        if st.button(f"Summarize with {st.session_state.llm_option}"):
            with st.spinner(f"Summarizing using {st.session_state.llm_option}..."):
                try:
                    if st.session_state.llm_option == "OpenAI (GPT)":
                        openai.api_key = st.session_state.api_key
                        result = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "Summarize the content."},
                                {"role": "user", "content": st.session_state.markdown_content},
                            ],
                            max_tokens=200,
                            temperature=0.7,
                        )

                        summary = result.choices[0].message.content.strip()
                        st.subheader("SUMMARY")
                        st.write(summary)


                    elif st.session_state.llm_option == "Gemini":
                        genai.configure(api_key=st.session_state.api_key)
                        model = genai.GenerativeModel("gemini-v1")
                        response = model.generate_content(
                            f"Summarize the content:\n\n{st.session_state.markdown_content}"
                        )
                        summary = response.text.strip()
                        st.subheader("SUMMARY")
                        st.write(summary)


                    elif st.session_state.llm_option == "Meta AI (LLaMA)":
                        summarizer = pipeline("summarization", model=st.session_state.api_key)
                        result = summarizer(
                            st.session_state.markdown_content, 
                            max_length=200, 
                            min_length=30, 
                            do_sample=False
                        )
                        summary = result[0]['summary_text']
                        st.subheader("SUMMARY")
                        st.write(summary)


                except Exception as e:
                    st.error(f"Error with {st.session_state.llm_option}: {e}")
