import os

from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient  # pymongo를 임포트 하기
import datetime
import hashlib
import jwt

SECRET_KEY = 'Eban5joDangStar'

client = MongoClient(
    'mongodb+srv://duck:1234@cluster0.8lepp.mongodb.net/Cluster0?retryWrites=true&w=majority')  # Atlas에서 가져올 접속 정보
db = client.dogstagram

app = Flask(__name__)


# 메인화면
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    most_good = list(db.board.find())

    most_good_board = sorted(most_good, key=(lambda x: len(x['good'])))[-1]
    board = {
        'title': most_good_board['title'],
        'comment': most_good_board['comment'],
        'nick': most_good_board['nick'],
        'file': '../static/boardImage/' + most_good_board['file'],
        'date': most_good_board['file'][5:15],
        'good': len(most_good_board['good'])
    }
    print(board)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('index.html', isOn="on", board = board)
    except jwt.ExpiredSignatureError:
        return render_template('index.html', isOn="off", board = board)
    except jwt.exceptions.DecodeError:
        return render_template('index.html', isOn="off", board = board)


# 게시물 등록하기
@app.route('/addboard')
def addboard():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('addboard.html', isOn="on")
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", redirectUrl="myboardlist"))
    except jwt.exceptions.DecodeError:
        # 로그인 후 원래 페이지로 돌아가기 위해 redirectUrl을 뿌려줌
        # 아래처럼 리다이렉트하면 브라우저 url이 /login?redirectUrl=addboard처럼 변경되고 login()
        # 함수가 호출되어 render_template('login.html') 로 login.html 화면이 나타난다.
        # 로그인 페이지를 렌더하는 login()함수에서 redirectUrl 쿼리 파라미터를 받아 사용하지 않고
        # 클라이언트에서 브라우저의 url을 파싱해서 로그인 요청이 완료되면 해당 페이지로 이동시킴!
        return redirect(url_for("login", redirectUrl="addboard"))


# 로그인
@app.route('/login')
def login():
    return render_template('login.html')


# 마이페이지
@app.route('/mypage')
def myPage():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
        result = {'id': userinfo['id'], 'pw': userinfo['pw'], 'nick': userinfo['nick']}
        return render_template('mypage.html', result=result)
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return redirect(url_for("/"))


# 게시물 전체보기
# jinja2 템플릿을 이용하기 위해 게시물의 제목, 사진, 작성자등을
# render_templates의 인자로 넘겨준다
@app.route('/boardlist')
def boardlist():
    token_receive = request.cookies.get('mytoken')
    # board의 데이터를 가공 후 boardlist 페이지로 넘겨줍니다!
    boards_ = reversed(list(db.board.find()))
    print(boards_, 1)
    boards = []

    for board in boards_:
        boards.append({
            'board_id': board['board_id'],
            'title': board['title'],
            'comment': board['comment'],
            'user_id': board['user_id'],
            'nick': board['nick'],
            'file': '../static/boardImage/' + board['file'],
            'date': board['file'][5:15],
            'good': len(board['good'])
        })
    # print해서 확인해봐용!

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('boardlist.html', isOn="on", boards=boards)
    except jwt.ExpiredSignatureError:
        return render_template('boardlist.html', isOn="off", boards=boards)
    except jwt.exceptions.DecodeError:
        return render_template('boardlist.html', isOn="off", boards=boards)


# 내자랑 전체보기
@app.route('/myboardlist')
def myboardlist():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # token에서 회원 아이디를 빼서 게시글 조회
        boards_ = reversed(list(db.board.find({'user_id': payload['id']})))
        boards = []
        for board in boards_:
            boards.append({
                'board_id': board['board_id'],
                'title': board['title'],
                'comment': board['comment'],
                'user_id': board['user_id'],
                'nick': board['nick'],
                'file': '../static/boardImage/' + board['file'],
                'date': board['file'][5:15],
                'good': len(board['good'])
            })
        print(boards)
        return render_template('myboardlist.html', isOn="on", boards=boards)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", redirectUrl="myboardlist"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", redirectUrl="myboardlist"))


# 내 자랑 하나보기
@app.route('/myboard/<board_id>')
def myboard(board_id):
    board_id_receive = board_id
    board_ = db.board.find_one({'board_id': board_id_receive})
    board = {
        "board_id": board_['board_id'],
        "title": board_['title'],
        "comment": board_['comment'],
        "file": '../static/boardImage/' + board_['file']
    }
    return render_template('myboard.html', board=board, isOn='on')


# 게시글 올리기 API
@app.route('/api/addboard', methods=['POST'])
def add_board():
    title_receive = request.form["title_give"]
    comment_receive = request.form["comment_give"]
    file_receive = request.files["file_give"]
    # static 폴더에 저장될 파일 이름 생성하기
    today = datetime.datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
    filename = f'file-{mytime}'
    # 확장자 나누기
    extension = file_receive.filename.split('.')[-1]
    # static 폴더에 저장
    save_to = f'static/boardImage/{filename}.{extension}'
    file_receive.save(save_to)

    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        id = payload['id']
        nick = payload['nick']
    except jwt.ExpiredSignatureError:
        return redirect(url_for("", msg="로그인이 필요합니다!"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("", msg="로그인이 필요합니다!"))

    # DB에 저장
    doc = {
        'board_id': filename,
        'title': title_receive,
        'user_id': id,
        'comment': comment_receive,
        'file': f'{filename}.{extension}',
        'nick': nick,
        'good': []
    }
    db.board.insert_one(doc)

    return jsonify({'msg': '업로드 완료!'})


# 게시글 수정하기 API
@app.route('/api/editboard', methods=['PUT'])
def edit_board():
    title_receive = request.form["title_give"]
    comment_receive = request.form["comment_give"]
    file_receive = request.files["file_give"]
    board_id_receive = request.form["board_id_give"]
    prev_file_receive = request.form["prev_file_give"]
    db.board.update_one({'board_id': board_id_receive},
                        {'$set': {'title': title_receive}})
    db.board.update_one({'board_id': board_id_receive},
                        {'$set': {'comment': comment_receive}})

    # 만약 이미지 파일이 변경되지 않을때 보내주는 foo.txt 파일이 아닐 경우에는
    # 파일을 다시 저장 한 후, 기존의 파일은 삭제
    if file_receive.filename != 'foo.txt':
        today = datetime.datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
        filename = f'file-{mytime}'
        extension = file_receive.filename.split('.')[-1]
        save_to = f'static/boardImage/{filename}.{extension}'
        file_receive.save(save_to)
        # 기존 파일의 경로를 받아서 삭제!
        # 기존 파일은 삭제 맨앞의 .을 하나 떼어야 정확한 경로로 갈 수 있다.
        # html 페이지가 있는 경로와 app.py의 경로가 다르므로!
        os.remove(prev_file_receive[1:])

        db.board.update_one({'board_id': board_id_receive},
                            {'$set': {'file': f'{filename}.{extension}'}})

    return jsonify({'result': 'success'})


# 게시글 삭제하기 API
@app.route('/api/deleteboard', methods=['DELETE'])
def delete_board():
    board_id_receive = request.args.get('board_id_give');
    prev_img = db.board.find_one({'board_id': board_id_receive})

    os.remove('./static/boardImage/' + prev_img['file'])
    db.board.delete_one({'board_id': board_id_receive})

    return jsonify({'result': 'success'})


# 좋아요 기능 API
@app.route('/api/goodboard', methods=['POST'])
def good_board():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['id']
    except jwt.ExpiredSignatureError:
        return jsonify({'result': 'fail', 'msg': "로그인이 필요합니다!"})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': "로그인이 필요합니다!"})
    board_id_receive = request.form['board_id_give']

    good = db.board.find_one({"board_id": board_id_receive})['good']
    if user_id in good:
        good.remove(user_id)
    else:
        good.append(user_id)
    db.board.update_one({'board_id': board_id_receive}, {'$set': {'good': good}})
    print(good)
    return jsonify({'result': 'success', 'good': good})


###### 로그인과 회원가입을 위한 API #####

## 아이디 중복확인
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    userid_receive = request.form['userid_give']
    exists = bool(db.user.find_one({"id": userid_receive}))
    ## 변수명이 잘못되어 테스트함
    # print(f'유저아이디 : {userid_receive}, bool: {exists}')
    return jsonify({'result': 'success', 'exists': exists})


## 회원가입 API
@app.route('/api/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']
    ## 해쉬를 이용해 pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.user.insert_one({'id': id_receive, 'pw': pw_hash, 'nick': nickname_receive})

    return jsonify({'result': 'success'})


## 로그인 API
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    ## 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        payload = {
            'id': id_receive,
            'nick': result['nick'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=300)
        }
        ## 오류나면 이거로
        # token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        ## token과 redirectURL을 -> 클라이언트에서 로그인 후 이 정보로 리다이이렉트
        return jsonify({'result': 'success', 'token': token})
    ## 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# 비밀번호 확인 API (비밀번호 변경할 때 현재 비밀번호와 )
@app.route('/api/checkpw', methods=['POST'])
def checkPW():
    token_receive = request.cookies.get('mytoken')
    pw_receive = request.form["pw_give"]
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
        pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

        if (pw_hash == userinfo['pw']):
            return jsonify({'result': 'success'})
        else:
            return jsonify({'result': 'fail'})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return redirect(url_for("login", redirectUrl="mypage"))


# 회원정보수정 API - 선용
@app.route('/api/changeinfo', methods=['POST'])
def changeInfo():
    id_receive = request.form["id_give"]
    pw_receive = request.form["pw_give"]
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    db.user.update_one({'id': id_receive}, {'$set': {'pw': pw_hash}})
    return jsonify({'result': 'success'})


# 회원탈퇴 API - 선용
@app.route('/api/signout', methods=['POST'])
def deleteInfo():
    id_receive = request.form["id_give"]
    db.user.delete_one({'id': id_receive})
    files = list(db.board.find({'user_id': id_receive}))
    for file in files:
        os.remove('./static/boardImage/' + file['file'])
    db.board.delete_many({'user_id': id_receive})
    return jsonify({'result': 'success'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
