import os
import streamlit as st
from utils import extract_archive, process_pdf_files, extract_details_from_pdf, detect_missing_info
from conversation import get_text_chunks, get_vectorstore, get_conversation_chain

def main():
    st.set_page_config(page_title="Document Quality Check")

    # Apply custom CSS
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
        body {font-family: 'Roboto', sans-serif;}
        {custom_css}
        </style>
        """.replace("{custom_css}", open("style.css").read()),
        unsafe_allow_html=True
    )

    # Add a header image
    st.image("header_image.png", use_column_width=True)
    predefined_questions = {
        "Revision Number": ["What is the Revision number or Rev it should be like A or B and maybe a number like 00 and give me ?"],
        "Date": ["What is the Date that has been mentioned in the text?"],
        "Document Number": ["What is the document number?"],
        "Project Title": ["What is the project title?"],
        "Project Number": ["What is the project number?"],
        "Customer Name": ["What is the customer name?"]
    }
    # Sidebar navigation
    with st.sidebar:
        st.markdown(
            """
            <ul class="sidebar-nav">
                <li><a href="#" id="home-link" class="nav-link active">Home</a></li>
                <li><a href="#" id="about-link" class="nav-link">About the Application</a></li>
                <li><a href="#" id="docs-link" class="nav-link">Documentation</a></li>
            </ul>
            """, unsafe_allow_html=True
        )

    # Initialize session state for page navigation
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'

    # JavaScript to handle navigation
    st.markdown(
        """
        <script>
        document.getElementById('home-link').onclick = function() {
            window.parent.postMessage({page: 'home'}, '*');
        };
        document.getElementById('about-link').onclick = function() {
            window.parent.postMessage({page: 'about'}, '*');
        };
        document.getElementById('docs-link').onclick = function() {
            window.parent.postMessage({page: 'docs'}, '*');
        };
        </script>
        """, unsafe_allow_html=True)

    # Handle page change events
    st.markdown(
        """
        <script>
        window.addEventListener('message', (event) => {
            const { page } = event.data;
            window.sessionStorage.setItem('page', page);
            window.location.reload();
        });
        </script>
        """, unsafe_allow_html=True)

    # Load the current page from session storage
    current_page = st.session_state.get('page', 'home')

    # Display the appropriate page content
    if current_page == 'home':
        st.header("Document Quality Check")
        st.subheader("Upload Document")
        uploaded_file = st.file_uploader("Upload a compressed file (ZIP or RAR) containing PDFs:", type=["zip", "rar"])

        if uploaded_file is not None:
            if 'all_document_details' in st.session_state:
                del st.session_state['all_document_details']
            if 'pdf_texts' in st.session_state:
                del st.session_state['pdf_texts']

            with st.spinner("Extracting documents..."):
                extract_archive(uploaded_file, "extracted_pdfs")
                st.success("Extraction complete!")

            pdf_files = [os.path.join("extracted_pdfs", f) for f in os.listdir("extracted_pdfs") if f.endswith(".pdf")]

            if st.button("Submit"):
                with st.spinner("Processing..."):
                    pdf_texts = process_pdf_files(pdf_files)
                    all_document_details = {}

                    for pdf_filename, pdf_text in pdf_texts.items():
                        document_details = extract_details_from_pdf(pdf_text, predefined_questions)
                        missing_info = detect_missing_info(document_details)
                        status = "Good" if not missing_info else "Corrupted"
                        all_document_details[pdf_filename] = {"status": status, "missing_info": missing_info, "details": document_details}

                    st.session_state.all_document_details = all_document_details
                    st.session_state.pdf_texts = pdf_texts

        if 'all_document_details' in st.session_state:
            st.subheader("Document Status:")
            for pdf_filename, details in st.session_state.all_document_details.items():
                if details["status"] == "Good":
                    st.success(f"**{pdf_filename}**: Good")
                else:
                    st.error(f"**{pdf_filename}**: Corrupted")
                    st.write("Missing Information:")
                    for missing in details["missing_info"]:
                        st.write(f"- {missing}")

    elif current_page == 'about':
        st.header("About the Application")
        st.write("""
        This application allows users to upload compressed files containing PDF documents for quality checking.
        It extracts key details from the first page of each PDF and flags documents that are missing any required information.
        """)

    elif current_page == 'docs':
        st.header("Documentation")
        st.write("""
        ## Instructions
        1. **Upload a ZIP or RAR file** containing PDF documents.
        2. **Submit** to process the documents.
        3. **View the status** of each document.

        ## Features
        - **Text Extraction**: Extracts text from the first page of each PDF document.
        - **Detail Extraction**: Identifies key details such as Revision Number, Date, Document Number, Project Title, Project Number, and Customer Name.
        - **Quality Check**: Flags documents as "Corrupted" if any key details are missing.

        ## FAQ
        **Q: What file formats are supported for upload?**
        A: The application supports ZIP and RAR files containing PDF documents.

        **Q: How are missing details identified?**
        A: The application uses predefined questions to extract specific details from the text. If any details are not found, the document is flagged as corrupted.
        """)

if __name__ == '__main__':
    main()

