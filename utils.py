import os
import zipfile
import rarfile
import shutil
import fitz
from conversation import get_text_chunks , get_vectorstore,get_conversation_chain,llm,embeddings
def extract_archive(archive_file, extract_path):
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    os.makedirs(extract_path)
    
    filename = archive_file.name
    if filename.endswith('.zip'):
        with zipfile.ZipFile(archive_file, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    elif filename.endswith('.rar'):
        with rarfile.RarFile(archive_file, 'r') as rar_ref:
            rar_ref.extractall(extract_path)

def extract_text_from_pdf(file_path, page_num):
    pdf_document = fitz.open(file_path)
    page = pdf_document.load_page(page_num)
    text = page.get_text()
    pdf_document.close()
    return text

def process_pdf_files(pdf_files):
    pdf_texts = {}
    for pdf_file in pdf_files:
        raw_text = extract_text_from_pdf(pdf_file,0)
        pdf_texts[os.path.basename(pdf_file)] = raw_text
    return pdf_texts

def extract_details_from_pdf(pdf_text, predefined_questions):
    text_chunks = get_text_chunks(pdf_text)
    vectorstore = get_vectorstore(text_chunks, embeddings)
    conversation = get_conversation_chain(vectorstore, llm)
    
    document_details = {}
    for detail, questions in predefined_questions.items():
        detail_answers = []
        for question in questions:
            response = conversation({'question': question})
            answer = response['chat_history'][-1].content
            detail_answers.append(answer.strip())
        document_details[detail] = detail_answers
    return document_details

def detect_missing_info(document_details):
    missing_info = []
    for detail, answers in document_details.items():
        if not answers or any(answer == 'none' for answer in answers):
            missing_info.append(detail)
    return missing_info
