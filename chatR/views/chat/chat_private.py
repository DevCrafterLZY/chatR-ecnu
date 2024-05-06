import os
import json
from flask import Blueprint, request, jsonify

from chatR.tools.retriever import retriever
from chatR.tools.sqlhelper import db
from chatR.tools.llm import llm
from chatR.tools.store import faiss_engine
from chatR.tools.translator import translator
from chatR.tools.utils import private_get_chat_history_list, process_raw_docs
from chatR.config.config import config

chat_private_bp = Blueprint('chat_private', __name__)


async def private_get_answer(i_id, files, history, question):
    directories = []
    file_names = []
    en_question = translator.translate(question)
    print(en_question)
    for file in files:
        filename = file[1]
        file_names.append(filename)
        filename_without_extension = os.path.splitext(filename)[0]
        directory = os.getcwd() + '/chatR/static/pdf/' + str(i_id) + '/' + filename_without_extension
        directories.append(directory)
    print("private get_chat_chain start ")

    vector_store = faiss_engine.load_vector_store(directories)
    file_names_str = '\n'.join([f"{i + 1}. {file}" for i, file in enumerate(file_names)])

    questions_list = llm.get_questions(file_names_str, history, en_question)

    print("questions: ", questions_list)
    relevant_docs = await retriever.rrf_get_relevant_documents(questions_list, vector_store)
    print("private relevant docs: ")
    for doc in relevant_docs:
        print(doc.metadata)
    if len(relevant_docs) > 0:
        context, resources, is_mult_files = process_raw_docs(relevant_docs)
        answer = llm.get_a(file_names_str, history, context, question)
        return answer, resources
    else:
        return "抱歉，根据已知内容无法回答该问题。", []


@chat_private_bp.route('/private_mind_map', methods=['POST'])
def private_get_mind_map():
    i_id = request.json.get('i_id')
    mind_map = db.fetchone('select * from item where i_id = %s', i_id)[4]
    print("private_mind_map:", mind_map)
    return jsonify(json.loads(mind_map))


@chat_private_bp.route('/private_history_message', methods=['POST'])
def private_history_message():
    c_id = request.json.get('c_id')
    m_id = 1
    history_messages = db.fetchall('select * from message where c_id = %s order by q_time', c_id)
    processed_message_items = []
    for item in history_messages:
        processed_message_items.append({'id': m_id, 'role': 'H', 'message': item[2]})
        m_id += 1
        message_resources = json.loads(item[5]) if item[5] else {}
        processed_message_items.append({'id': m_id, 'role': 'R', 'message': item[3], 'resources': message_resources})
    return jsonify(
        {
            'history_messages': processed_message_items
        }
    )


@chat_private_bp.route('/private_pdf_path', methods=['POST'])
def private_pdf_path():
    c_id = request.json.get('c_id')
    chat = db.fetchone('select * from chat where c_id = %s', c_id)
    i_id = chat[1]
    chat_file = db.fetchone('select * from chat_file where c_id = %s', c_id)
    file = db.fetchone('select * from file where f_id = %s', chat_file[1])
    filename = file[1]
    filename_without_extension = os.path.splitext(filename)[0]
    path = config.url + '/static/pdf/' + str(i_id) + '/' + filename_without_extension + '/' + filename
    print("c_id: ", c_id, " path: ", path)
    return jsonify(
        {
            'pdf_path': path
        }
    )


@chat_private_bp.route('/private_send_message', methods=['POST'])
async def private_send_message():
    message = request.json['message']
    c_id = request.json['c_id']
    print('c_id:', c_id, ' message: ', message)
    chats = db.fetchall('select * from chat_file where c_id = %s', c_id)
    print(chats)
    files = []
    for chat in chats:
        files.append(db.fetchone('select * from file where f_id = %s', chat[1]))
    chat = db.fetchone('select * from chat where c_id = %s', c_id)
    i_id = chat[1]
    history = private_get_chat_history_list(c_id, 1)
    answer, resources = await private_get_answer(i_id, files, history, message)
    db.addone('INSERT INTO message (c_id,q_context, a_content,a_source_documents) VALUES (%s,%s, %s,%s)'
              , c_id, message, answer, json.dumps(resources, ensure_ascii=False), )
    return jsonify(
        {
            'status': 'success',
            'answer': answer,
            'resources': resources
        }
    )
