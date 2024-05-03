import asyncio

from flask import request, Blueprint, jsonify
import os
import json

from chatR.tools.llm import llm
from chatR.tools.mind_map import generate_mind_map
from chatR.tools.sqlhelper import db
from chatR.tools.store import faiss_engine
from chatR.tools.utils import save_file, pdf2vector

home_public_bp = Blueprint('home_public', __name__)


async def process_public_file(i_id, f):
    filename_without_extension = os.path.splitext(f.filename)[0]
    directory = (os.getcwd() + '/chatR/static/ppdf/' +
                 i_id + '/' + filename_without_extension)
    file_path = save_file(f, directory)
    print("directory: ", file_path, 'file saved')
    pdf2vector(file_path, directory)

    vector_store = faiss_engine.load_vector_store([directory])
    if llm.model_name == "gpt-3.5-turbo":
        introduce = await llm.get_introduce(vector_store)
    else:
        introduce = llm.get_introduce(vector_store)

    print('introduce ', introduce)

    c_id = db.add_chat('INSERT INTO public_chat (pi_id) VALUES (%s)', int(i_id))
    f_id = db.add_file('INSERT INTO public_file (pf_name, pf_introduce) '
                       'VALUES (%s, %s)', f.filename, introduce)

    db.addone('INSERT INTO public_chat_file(pc_id, pf_id) values (%s, %s)', c_id, f_id)

    return {'c_id': c_id, 'f_id': f_id, 'f_name': f.filename, 'f_introduce': introduce}


async def create_public_item(i_id, files):
    i_id = str(i_id)

    tasks = [process_public_file(i_id, f) for f in files]
    chats = await asyncio.gather(*tasks)

    context = ""
    default_c_id = db.add_chat('INSERT INTO public_chat (pi_id,p_chat_type) VALUES (%s,%s)', int(i_id), 1)
    for chat in chats:
        context += "id: " + str(chat['f_id']) + ";概述: " + chat['f_introduce'] + '\n'
        db.addone('INSERT INTO public_chat_file(pc_id, pf_id) values (%s, %s)', default_c_id, chat['f_id'])

    classification = llm.get_classification(context)

    mind_map = generate_mind_map(i_id, default_c_id, chats, classification, 'public')
    db.update("UPDATE public_item SET pi_mind_map = %s WHERE pi_id = %s"
              , json.dumps(mind_map, ensure_ascii=False), i_id)

    return default_c_id


@home_public_bp.route('/public_uploader', methods=['POST'])
async def public_file_uploader():
    if request.method == 'POST':
        i_name = request.form['item']
        files = request.files.getlist('files')
        item = db.add_public_item('INSERT INTO  public_item(pi_name) VALUES (%s)', i_name)
        default_c_id = await create_public_item(item[0], files)

        return jsonify(
            {
                'success': True,
                'i_id': int(item[0]),
                'c_id': int(default_c_id),
            }
        )


@home_public_bp.route('/public_item', methods=['POST'])
def public_history_item():
    public_items = db.fetchall('select public_item.pi_id,pi_name,pc_id ,pi_create_time '
                               'from public_item inner join public_chat on public_item.pi_id = public_chat.pi_id '
                               'where p_chat_type = 1 '
                               'order by pi_create_time desc ')

    processed_public_items = [{'id': item[0], 'name': item[1], 'default_c_id': item[2], 'create_time': str(item[3])}
                              for item in public_items]
    return jsonify(
        {
            'public_items': processed_public_items
        }
    )
