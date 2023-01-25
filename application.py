from flask import *
import random, string 
import randomID_generation 
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import os
import psycopg2
import time

app = Flask(__name__)
socketio = SocketIO(app)

def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='tungdo',
                            user="tungdo",
                            password="tung2001")
    return conn

def increase_speed_up(lecture_id):
    #create speed up entry
    db_conn = get_db_connection() 
    cur = db_conn.cursor() 
    cur.execute('INSERT INTO speed_up (lecture_id, timestamp, resolved)'
    'VALUES (%s, %s, %s) RETURNING id',
    (lecture_id, int(time.time()), False))
    id = cur.fetchone()[0]
    db_conn.commit()
    cur.close()
    db_conn.close()
    #update lecture data table 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE lecture2 SET speed_up=speed_up+1 WHERE lecture_id=%s;" % lecture_id) 
    conn.commit()
    cur.close()
    conn.close() 
    return id 

def increase_slow_down(lecture_id):
    #create speed up entry
    db_conn = get_db_connection() 
    cur = db_conn.cursor() 
    cur.execute('INSERT INTO slow_down (lecture_id, timestamp, resolved)'
    'VALUES (%s, %s, %s) RETURNING id',
    (lecture_id, int(time.time()), False))
    id = cur.fetchone()[0]
    db_conn.commit()
    cur.close()
    db_conn.close()
    #update lecture data table 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE lecture2 SET slow_down=slow_down+1 WHERE lecture_id=%s;" % lecture_id) 
    conn.commit()
    cur.close()
    conn.close() 
    return id 

def get_lectureid_by_speedupid(id): 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM speed_up WHERE id = %s;' % id)
    speedup_data = cur.fetchall()
    lecture_id = speedup_data[0][1]
    cur.close()
    conn.close()
    return lecture_id

def get_lectureid_by_slowdownid(id): 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM slow_down WHERE id = %s;' % id)
    slowdown_data = cur.fetchall()
    lecture_id = slowdown_data[0][1]
    cur.close()
    conn.close()
    return lecture_id

def decrease_speed_up(speedup_id):
    #create speed up entry
    lecture_id = get_lectureid_by_speedupid(speedup_id)
    db_conn = get_db_connection() 
    cur = db_conn.cursor() 
    cur.execute("UPDATE speed_up SET resolved = %s WHERE id=%s;" % (True, speedup_id)) 
    db_conn.commit()
    cur.close()
    db_conn.close()
    #update lecture data table 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE lecture2 SET speed_up=speed_up-1 WHERE lecture_id=%s;" % lecture_id) 
    conn.commit()
    cur.close()
    conn.close() 

def decrease_slow_down(slowdown_id):
    lecture_id = get_lectureid_by_slowdownid(slowdown_id)
    db_conn = get_db_connection() 
    cur = db_conn.cursor() 
    cur.execute("UPDATE slow_down SET resolved = %s WHERE id=%s;" % (True, slowdown_id)) 
    db_conn.commit()
    cur.close()
    db_conn.close()
    #update lecture data table 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE lecture2 SET slow_down=slow_down-1 WHERE lecture_id=%s;" % lecture_id) 
    conn.commit()
    cur.close()
    conn.close() 

#routing application 
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
            #lecture_id = randomID_generation.generate_lectureID() 
            access_code = randomID_generation.generate_access_code()
            cur.execute('INSERT INTO lecture2 (access_code, lecture_name, speed_up, slow_down)'
            'VALUES (%s, %s, %s, %s)',
            (access_code, lecture_name, 0, 0))
            db_conn.commit()
            cur.close()
            db_conn.close()
            #get lecture_id
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM lecture2 WHERE access_code = \'%s\';' % access_code)
            lecture_data = cur.fetchall()
            lecture_id = lecture_data[0][0]
            cur.close()
            conn.close()
            return redirect(url_for('professor_lecture', lecture_id = lecture_id))

@app.route("/professor/<lecture_id>/", methods = ('GET', 'POST'))
def professor_lecture(lecture_id): 
    if request.method == 'GET': 
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM lecture2 WHERE lecture_id = %s;' % lecture_id)
        lecture_data = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('professor-lecture.html', lecture_data = lecture_data[0])

@app.route("/student/<access_code>/", methods = ('GET', 'POST'))
def student_lecture(access_code): 
    if request.method == 'GET': 
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM lecture2 WHERE access_code = \'%s\';' % access_code)
        lecture_data = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('student-lecture.html', lecture_data = lecture_data[0])
    if request.method == "POST": 
        question_content = request.form.get("question")
        question_time = int(time.time())
        #get lecture_id
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM lecture2 WHERE access_code = \'%s\';' % access_code)
        lecture_data = cur.fetchall()
        lecture_id = lecture_data[0][0]
        cur.close()
        conn.close()
        #create new question database entry
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO question (content, lecture_id, timestamp, resolved)'
        'VALUES (%s, %s, %s, %s)',
        (question_content, lecture_id, question_time, False))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(request.url)


@socketio.on('speed_up')
def speed_up(data): 
    lecture_id = data['lecture_id']
    id = increase_speed_up(lecture_id)
    join_room(lecture_id) 
    emit("speed_up", {"speed_up_id": id}, room=lecture_id)

@socketio.on('slow_down')
def slow_down(data):
    lecture_id = data['lecture_id']
    id = increase_slow_down(lecture_id)
    join_room(lecture_id) 
    emit("slow_down", {"slow_down_id": id}, room=lecture_id)

@socketio.on("expire_speed_up")
def expire_speed_up(data): 
    speed_up_id = data['speed_up_id']
    decrease_speed_up(speed_up_id) 

@socketio.on("expire_slow_down")
def expire_slow_down(data): 
    slow_down_id = data['slow_down_id']
    decrease_slow_down(slow_down_id) 

@socketio.on("join")
def join_room_client(data): 
    join_room(data) 
    
    
if __name__ == '__main__':
    socketio.run(app)


