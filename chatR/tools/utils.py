import os
import re
from collections import defaultdict
from typing import List
import hashlib
import random
import requests
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from chatR.config.config import config
from chatR.tools.pdf import PdfEngine
from chatR.tools.sqlhelper import db
from chatR.tools.store import faiss_engine


def get_document_chunks(
        text,
        chunk_size: int = 768,
        chunk_overlap: int = 200
) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        # chunk_size=768,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    return text_splitter.split_documents(text)


def pdf2vector(file_path, directory):
    print('pdf2vector start')
    pfd_engine = PdfEngine(file_path)
    raw_document = pfd_engine.get_pdf_document()
    document_chunks = get_document_chunks(raw_document)
    faiss_engine.save_vector_store(document_chunks, directory)
    print('pdf2vector success')


def save_file(file, directory) -> str:
    os.makedirs(directory, exist_ok=True)
    file_path = directory + '\\' + file.filename
    if os.path.exists(file_path):
        print(f"{file.filename} already exists, skipping...")
    file.save(file_path)
    return file_path


def private_get_chat_history(c_id, size=1) -> str:
    history_messages = db.fetchall('select * from message where c_id = %s order by q_time desc limit %s', c_id, size)
    history = ""
    for message in history_messages:
        human = "Human: " + message[2]
        ai = "You: " + message[3]
        history += "\n\n" + "\n".join([human, ai])
    return history


def public_get_chat_history(c_id, u_id, size=1) -> str:
    history_messages = db.fetchall('select * from public_message '
                                   'where pc_id = %s and u_id = %s '
                                   'order by q_time desc limit %s', c_id, u_id, size)
    history = ""
    for message in history_messages:
        human = "User: " + message[3]
        ai = "You: " + message[4]
        history += "\n\n" + "\n".join([human, ai])
    return history


def get_standalone_questions_list(
        standalone_questions_str: str, original_question: str  # TODO 可以尝试添加原问题
) -> List[str]:
    pattern = r"\d+\.\s(.*?)(?=\n\d+\.|\n|$)"

    matches = [
        match.group(1) for match in re.finditer(pattern, standalone_questions_str)
    ]
    if matches:
        return matches

    match = re.search(
        r"(?i)standalone[^\n]*:[^\n](.*)", standalone_questions_str, re.DOTALL
    )
    sentence_source = match.group(1).strip() if match else standalone_questions_str
    sentences = sentence_source.split("\n")

    return [
        re.sub(
            r"^\((\d+)\)\.? ?|^\d+\.? ?\)?|^(\d+)\) ?|^(\d+)\) ?|^[Qq]uery \d+: ?|^[Qq]uery: ?",
            "",
            sentence.strip(),
        )
        for sentence in sentences
        if sentence.strip()
    ]


def baidu_translate(query) -> str:
    salt = random.randint(0, 100000)

    app_id = config.baidu_app_id
    api_key = config.baidu_api_key

    api_https = 'https://fanyi-api.baidu.com/api/trans/vip/translate'

    sign_raw = str(app_id) + query + str(salt) + api_key
    md = hashlib.md5()
    md.update(sign_raw.encode('utf-8'))
    sign = md.hexdigest()

    try:
        response = requests.get(
            api_https +
            '?q=' + query +
            '&from=zh&to=en' +
            '&appid=' + app_id +
            '&salt=' + str(salt) +
            '&sign=' + sign
        )

        if response.status_code == 200:
            result = response.json().get('trans_result')
            if result:
                return result[0].get('dst')
    except Exception as e:
        print("Translation failed with error:", e)

    return query


def process_raw_docs(
        raw_docs: List[Document]
):
    merged_content = defaultdict(list)
    unique_sources = []
    for doc in raw_docs:
        doc.metadata['source'] = os.path.basename(doc.metadata['source'])
        if doc.metadata not in unique_sources:
            unique_sources.append(doc.metadata)
    print("sources are:", unique_sources)

    for resource in raw_docs:
        merged_content[resource.metadata['source']].append(resource.page_content.strip())

    if len(merged_content) > 1:
        mult_sources = True
        output = []
        for source, content_list in merged_content.items():
            merged_content_str = '\n'.join(content_list)
            output.append(f"Context: \"{merged_content_str}\",source: \"{source}\";")
        return '\n'.join(output), unique_sources, mult_sources
    else:
        mult_sources = False
        first_source = list(merged_content.keys())[0]
        return ' '.join(merged_content[first_source]), unique_sources, mult_sources
