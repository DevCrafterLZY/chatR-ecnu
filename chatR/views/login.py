import functools

from flask import jsonify
from flask import request, redirect, Blueprint, session
from chatR.tools.sqlhelper import db

login_bp = Blueprint('login', __name__)


def auth(func):  # 装饰器，没有登入返回login页面，用@auth调用
    @functools.wraps(func)
    def inner(*args, **kwargs):
        username = session.get('username')
        if not username:
            return redirect('http://localhost:8080/login')
        return func(*args, **kwargs)
    return inner


@login_bp.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    print(username, password)
    result = db.fetchone('select * from user where u_name = %s', username)
    if result is None:
        return jsonify(
            {
                'success': False,
                'message': '用户名不存在!'
            }
        )
    if result is not None and result[2] == password:
        session['username'] = username
        print(username, "login_success")
        return jsonify(
            {
                'success': True,
                'u_id': result[0],
                'u_role': result[3],
                'message': '登录成功'
            }
        )

    else:
        print("login_failed")
        return jsonify(
            {
                'success': False,
                'message': '密码错误!'
            }
        )

