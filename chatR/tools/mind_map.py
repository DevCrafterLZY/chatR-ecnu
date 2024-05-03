from typing import Dict, Any

from chatR.tools.sqlhelper import db


def generate_mind_map(i_id, default_c_id, file_info_list, categories, base_type) -> Dict[str, Any]:
    if base_type == 'public':
        add_chat_sql = 'INSERT INTO public_chat (pi_id,p_chat_type) VALUES (%s,%s)'
        add_c_f_sql = 'INSERT INTO public_chat_file(pc_id, pf_id) values (%s, %s)'
    else:
        add_chat_sql = 'INSERT INTO chat (i_id,chat_type) VALUES (%s,%s)'
        add_c_f_sql = 'INSERT INTO chat_file(c_id, f_id) values (%s, %s)'
    mind_map = {
        'mind_map': {
            'data': {
                'text': '文献总览',
                'expand': True,
                'mydata': {
                    'c_id': default_c_id,
                    'type': 'files'
                }
            },
            'children': []
        }
    }

    # 构建主题类别节点
    for category in categories:
        c_id = db.add_chat(add_chat_sql, int(i_id), 2)
        category_node = {
            'data': {
                'text': category['name'],
                'expand': True,
                'mydata': {
                    'c_id': c_id,
                    'type': 'files'
                }
            },
            'children': []

        }

        for file_id in category['children']:
            file_info = next((file_info for file_info in file_info_list if file_info['f_id'] == file_id), None)
            if file_info:
                file_node = {
                    'data': {
                        'text': file_info['f_name'],
                        'generalization': {
                            'text': file_info['f_introduce']
                        },
                        'expand': True,
                        'mydata': {
                            'c_id': file_info["c_id"],
                            'type': 'file'
                        }
                    }
                }
                category_node['children'].append(file_node)
                db.addone(add_c_f_sql, c_id, file_info['f_id'])
        mind_map['mind_map']['children'].append(category_node)
    return mind_map
