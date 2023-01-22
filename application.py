from flask import *
import random, string 
import randomID_generation 
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import os
import psycopg2

app = Flask(__name__)
socketio = SocketIO(app)

def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='tungdo',
                            user="tungdo",
                            password="tung2001")
    return conn


@app.route("/", methods = ('GET', 'POST'))
def home():
    if request.method == 'GET':
        return render_template('home.html')
    if request.method == 'POST': 
        lecture_name = request.form.get('lecture-name')
        access_code = request.form.get('access-code')
        if access_code: 
            return redirect(url_for('student_lecture', access_code=access_code))
        if lecture_name: 
            db_conn = get_db_connection() 
            cur = db_conn.cursor() 
            lecture_id = randomID_generation.generate_lectureID() 
            access_code = randomID_generation.generate_access_code()
            cur.execute('INSERT INTO lecture (lecture_id, access_code, lecture_name, speed_up, slow_down)'
            'VALUES (%s, %s, %s, %s, %s)',
            (lecture_id, access_code, lecture_name, 0, 0))
            db_conn.commit()
            cur.close()
            db_conn.close()
            return redirect(url_for('professor_lecture', lecture_id = lecture_id))

@app.route("/professor/<lecture_id>/", methods = ('GET', 'POST'))
def professor_lecture(lecture_id): 
    if request.method == 'GET': 
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM lecture WHERE lecture_id = \'%s\';' % lecture_id)
        lecture_data = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('professor-lecture.html', lecture_data = lecture_data[0])
    
@app.route("/student/<access_code>/", methods = ('GET', 'POST'))
def student_lecture(access_code): 
    if request.method == 'GET': 
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM lecture WHERE access_code = \'%s\';' % access_code)
        lecture_data = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('student-lecture.html', lecture_data = lecture_data[0])

@socketio.on('speed_up')
def speed_up(data): 
    data = data['data']
    print(data, flush=True)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE lecture SET speed_up=speed_up+1 WHERE lecture_id=\'%s\';" % data) 
    conn.commit()
    cur.close()
    conn.close()
    join_room(data) 
    emit("speed_up", room=data)

@socketio.on('slow_down')
def slow_down(data):
    data = data['data']
    print(data, flush=True)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE lecture SET slow_down=slow_down+1 WHERE lecture_id=\'%s\';" % data) 
    conn.commit()
    cur.close()
    conn.close()
    join_room(data) 
    emit("slow_down", room=data)


@socketio.on("join")
def join_room_client(data): 
    join_room(data) 
    
    
if __name__ == '__main__':
    socketio.run(app)


