import asyncio

from flask import request, Blueprint, jsonify
import os
import json

from chatR.tools.store import faiss_engine
from chatR.tools.utils import save_file, pdf2vector
from chatR.tools.llm import llm
from chatR.tools.mind_map import generate_mind_map
from chatR.tools.sqlhelper import db

home_private_bp = Blueprint('home_private', __name__)


async def process_private_file(i_id, f):
    filename_without_extension = os.path.splitext(f.filename)[0]
    directory = (os.getcwd() + '\\chatR\\static\\pdf\\' +
                 i_id + '\\' + filename_without_extension)
    file_path = save_file(f, directory)
    print("directory: ", file_path, 'file saved')

    pdf2vector(file_path, directory)

    vector_store = faiss_engine.load_vector_store([directory])
    introduce = await llm.aget_introduce(vector_store)

    print('introduce ', introduce)

    c_id = db.add_chat('INSERT INTO chat (i_id) VALUES (%s)', int(i_id))
    f_id = db.add_file('INSERT INTO file (f_name,f_introduce) VALUES (%s, %s)',
                       f.filename, introduce)
    db.addone('INSERT INTO chat_file(c_id, f_id) values (%s, %s)', c_id, f_id)

    return {'c_id': c_id, 'f_id': f_id, 'f_name': f.filename, 'f_introduce': introduce}


async def create_item(i_id, files):
    i_id = str(i_id)

    tasks = [process_private_file(i_id, f) for f in files]
    chats = await asyncio.gather(*tasks)

    context = ""
    default_c_id = db.add_chat('INSERT INTO chat (i_id,chat_type) VALUES (%s,%s)', int(i_id), 1)
    for chat in chats:
        context += "id: " + str(chat['f_id']) + ";概述: " + chat['f_introduce'] + '\n'
        db.addone('INSERT INTO chat_file(c_id, f_id) values (%s, %s)', default_c_id, chat['f_id'])

    classification = llm.get_classification(context)
    mind_map = generate_mind_map(i_id, default_c_id, chats, classification, 'private')
    db.update("UPDATE item SET i_mind_map = %s WHERE i_id = %s", json.dumps(mind_map, ensure_ascii=False), i_id)
    return default_c_id


@home_private_bp.route('/private_uploader', methods=['POST'])
async def private_file_uploader():
    if request.method == 'POST':
        i_name = request.form['item']
        files = request.files.getlist('files')
        username = request.form['username']
        user = db.fetchone('select u_id from user where u_name = %s', username)
        item = db.add_item('INSERT INTO  item(i_name, u_id) VALUES (%s, %s)', i_name, user[0])
        default_c_id = await create_item(item[0], files)

        return jsonify(
            {
                'success': True,
                'i_id': int(item[0]),
                'c_id': int(default_c_id)
            }
        )


@home_private_bp.route('/private_item', methods=['POST'])
def private_history_item():
    username = request.json.get('username')
    user = db.fetchone('select u_id from user where u_name = %s', username)
    history_items = db.fetchall('select item.i_id,i_name,c_id ,i_create_time '
                                'from item inner join chat on item.i_id = chat.i_id '
                                'where u_id = %s and chat_type = 1 '
                                'order by i_create_time desc ', user[0])

    processed_history_items = [{'id': item[0], 'name': item[1], 'default_c_id': item[2], 'create_time': str(item[3])}
                               for item in history_items]
    return jsonify(
        {
            'history_items': processed_history_items
        }
    )
