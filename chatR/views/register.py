from flask import request, Blueprint, jsonify
from chatR.tools.sqlhelper import db

register_bp = Blueprint('register', __name__)


@register_bp.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    confirm_password = request.json.get('confirm_password')

    if len(username) > 20 or len(username) < 4:
        return jsonify({'success': False, 'message': '用户名需要在4到20位之间'})

    if len(password) > 20 or len(password) < 6:
        return jsonify({'success': False, 'message': '密码需要在6到20位之间'})

    if password != confirm_password:
        return jsonify({'success': False, 'message': '密码与确认密码不匹配'})

    existing_user = db.fetchone('SELECT * FROM user WHERE u_name = %s', username)
    if existing_user:
        return jsonify({'success': False, 'message': '用户名已存在'})

    db.addone('INSERT INTO user (u_name, u_pwd, u_role) VALUES (%s, %s, %s)', username, password, 'user')
    return jsonify({'success': True, 'message': '注册成功，请登录'})
