import calendar
import hashlib
import os
import sys
from datetime import datetime
from waitress import serve
import base64
import MySQLdb.cursors
import pytz
from flask import Flask, render_template, jsonify, request, make_response, session, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_restful import Api, Resource, reqparse
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
import face_comparision
import my_forms
from my_forms import AddForm
from functools import wraps

app = Flask(__name__)
app._static_folder = "./templates/static"
app.config['SECRET_KEY'] = '3141592653589793238462643383279502884197169399'
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'GAtt'
mysql = MySQL(app)
api = Api(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir, "uploaded_images/source/")

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)


# def checker():
#     if 'user_name' in session:

class AddStudentForm(FlaskForm):
    courseid = StringField('courseid', validators=[DataRequired(), Length(min=2, max=20)])
    studentid = StringField('studentid', validators=[DataRequired(), Length(min=2, max=20)])
    studentname = StringField('studentname', validators=[DataRequired(), Length(min=2, max=50)])
    studentbranch = StringField('studentbranch', validators=[DataRequired(), Length(min=2, max=80)])
    studentyear = StringField('studentyear', validators=[DataRequired(), Length(min=2, max=10)])
    studentsection = StringField('studentsection', validators=[DataRequired(), Length(min=1, max=10)])
    studentimage = FileField('studentimage',
                             validators=[FileAllowed(photos, 'Image Only!'), FileRequired('Choose a file!')])
    submit = SubmitField('Add Student')


class AdminLoginForm(FlaskForm):
    userName = StringField('userName', validators=[DataRequired(), Length(min=2, max=20)])
    password = StringField('password', validators=[DataRequired(), Length(min=4, max=20)])
    submit = SubmitField('submit')


class AETimeTable(FlaskForm):
    facultyId = StringField('facultyId')
    branch = StringField('branch')
    subject = StringField('subject')
    courseId = StringField('courseId')
    classId = StringField('classId')
    weekday = StringField('weekday')
    startTime = StringField('startTime')
    endTime = StringField('endTime')
    section = StringField('section')
    startYear = StringField('startYear')
    endYear = StringField('endYear')
    sem = StringField('sem')
    submit = SubmitField('submit')


class ETimeTable(FlaskForm):
    facultyId = StringField('facultyId')
    classId = StringField('classId')
    courseId = StringField('courseId')
    branch = StringField('branch')
    sec = StringField('sec')
    sem = StringField('sem')
    subject = StringField('subject')
    day = StringField('day')
    sessions = StringField('sessions')
    year = StringField('year')
    submit = SubmitField('submit')


class FacEd(FlaskForm):
    faculE = StringField('faculE')
    submit = SubmitField('submit')


def login_required(arg):
    @wraps(arg)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return arg(*args, **kwargs)
        else:
            flash("Login to Continue")
            return redirect(url_for('loginPage'))

    return wrap


# getData
@app.route('/home', methods=['GET', 'POST'])
@login_required
def addUser():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''SELECT * FROM `users`''')
    data = cursor.fetchall()
    form = AddForm()
    if form.validate_on_submit():
        userid = form.userid.data
        name = form.username.data
        email = form.email.data
        password = (hashlib.sha256(form.password.data.encode())).hexdigest()
        try:
            if cursor.execute('''INSERT INTO `users` VALUES(NULL, %s, %s, %s, %s)''', (userid, name, email, password)):
                return render_template("message.html", msg="Added User Successfully")
            else:
                return render_template("message.html", msg="Failed to adding User")
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            return render_template("message.html", msg=e)
        finally:
            mysql.connection.commit()
            cursor.close()
    return render_template('index.html', form=form, data=data)


@app.route('/home/timeTable', methods=['GET', 'POST'])
@login_required
def timeTable():
    form = AETimeTable()
    form1 = FacEd()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''SELECT * FROM `users`''')
    data = cursor.fetchall()
    mysql.connection.commit()
    cursor.close()
    datas = {}
    if form.validate_on_submit():
        subNewPeriod()

    if form1.validate_on_submit():
        facid = form1.faculE.data
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''SELECT * FROM `time_table` WHERE user_id=%s ORDER BY id DESC''', [facid])
        datas = cursor.fetchall()
        mysql.connection.commit()
        cursor.close()
        return render_template('timeTable.html', form=form, form1=form1, data=data, datas=datas)
    if request.method == "GET":
        return render_template('timeTable.html', form=form, form1=form1, data=data, datas=datas)
    if request.method == "POST":
        name = form.facultyId.data
        flash(name)
        return render_template('timeTable.html', form=form, form1=form1, data=data, datas=datas)


def subNewPeriod():
    form = AETimeTable()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    facultyId = form.facultyId.data
    courseId = form.courseId.data
    classId = form.classId.data
    sec = form.section.data
    branch = form.branch.data
    sem = form.branch.data
    subj = form.subject.data
    day = form.weekday.data
    sessions = form.startTime.data + " to " + form.endTime.data
    year = form.startYear.data + "-" + form.endYear.data
    try:
        query = '''INSERT INTO `time_table` (`id`, `class_id`, `course_id`, `sec`, `branch`, `sem`, 
            `subj`, `user_id`, `day`, `sessions`, `year`) VALUES (NULL,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        if cursor.execute(query, (classId, courseId, sec, branch, sem, subj, facultyId, day, sessions, year)):
            flash("Added period in Timetable for FacultyID: " + facultyId)
        else:
            flash("Failed to add Period in Timetable")
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        flash("error:'" + e + "' occurred, contact Administrator")
    mysql.connection.commit()
    cursor.close()
    return redirect("/home/timeTable/" + facultyId)


@app.route('/home/timeTable/delete/<facultyId>/<idP>', methods=['GET', 'POST'])
@login_required
def timeTableDelete(facultyId, idP):
    facId = str(facultyId)
    idP = str(idP)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        if cursor.execute('''DELETE FROM `time_table` WHERE `id`=%s''', [idP]):
            flash("Period deleted from Timetable")
        else:
            flash("Failed to delete Period from Timetable")
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        flash("error:'" + e + "' occurred, contact Administrator")
    mysql.connection.commit()
    cursor.close()
    return redirect('/home/timeTable/' + facultyId)


@app.route('/home/timeTable/<facultyId>', methods=['GET', 'POST'])
@login_required
def timeTablewid(facultyId):
    form = AETimeTable()
    form1 = FacEd()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''SELECT * FROM `users`''')
    data = cursor.fetchall()
    mysql.connection.commit()
    cursor.close()
    datas = {}
    if form.validate_on_submit():
        subNewPeriod()
    if facultyId is not None:
        facid = facultyId
        form1.faculE.data = facid
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''SELECT * FROM `time_table` WHERE user_id=%s ORDER BY id DESC''', [facid])
        datas = cursor.fetchall()
        mysql.connection.commit()
        cursor.close()
        return render_template('timeTable.html', form=form, form1=form1, data=data, datas=datas)
    if form1.validate_on_submit():
        facid = form1.faculE.data
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''SELECT * FROM `time_table` WHERE user_id=%s ORDER BY id DESC''', [facid])
        datas = cursor.fetchall()
        mysql.connection.commit()
        cursor.close()
        return render_template('timeTable.html', form=form, form1=form1, data=data, datas=datas)
    if request.method == "GET":
        return render_template('timeTable.html', form=form, form1=form1, data=data, datas=datas)
    if request.method == "POST":
        name = form.facultyId.data
        flash(name)
        return render_template('timeTable.html', form=form, form1=form1, data=data, datas=datas)


@app.route('/home/timeTable/<idP>/<user_id>/<class_id>/<course_id>/<sec>/<branch>/<sem>/<subj>/<day>/<sessions>/<year>',
           methods=['GET', 'POST'])
@login_required
def ttimeTable(idP, user_id, class_id, course_id, sec, branch, sem, subj, day, sessions, year):
    form = ETimeTable()
    form.facultyId.data = user_id
    form.classId.data = class_id
    form.courseId.data = course_id
    form.sec.data = sec
    form.branch.data = branch
    form.sem.data = sem
    form.subject.data = subj
    form.day.data = day
    form.sessions.data = sessions
    form.year.data = year
    if request.method == "POST":
        if form.validate_on_submit():
            form = ETimeTable()
            facultyId = user_id
            class_id = form.classId.data
            course_id = form.courseId.data
            sec = form.sec.data
            branch = form.branch.data
            sem = form.sem.data
            subj = form.subject.data
            day = form.day.data
            sessions = form.sessions.data
            year = form.year.data
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            try:
                query = '''UPDATE `time_table` SET `class_id`="''' + class_id + '''",`course_id`="''' + course_id + '''",
            `sec`="''' + sec + '''",`branch`="''' + branch + '''",`sem`="''' + sem + '''",`subj`="''' + subj + '''",`day`="''' + day + '''",
            `sessions`="''' + sessions + '''",`year`="''' + year + '''" WHERE `id`=''' + idP + ''' AND `user_id`="''' + facultyId + '''"'''
                if cursor.execute(query):
                    flash("Timetable Updated!")
                else:
                    flash("Timetable Not Update!" + str(mysql.connection.error))
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                flash("error:'" + e + "' occurred, contact Administrator")
            finally:
                mysql.connection.commit()
                cursor.close()
            return redirect("/home/timeTable/" + user_id)
    return render_template('edit_timetable.html', form=form)


@app.route('/login', methods=['GET'])
def loginPage():
    session.pop('logged_in', None)
    form = AdminLoginForm()
    return render_template('login.html', form=form, msg_s="", msg_e="")


# @app.route('/getTT', methods=['POST'])
# def getTT():
#     user_id = request.json['user_id']
#     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     if cursor.execute('''SELECT * FROM `time_table` WHERE user_id=%s''', user_id):
#         data = cursor.fetchall()
#     mysql.connection.commit()
#     cursor.close()
#     return jsonify(data)


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('logged_in', None)
    form = AdminLoginForm()
    return render_template('login.html', form=form, msg_s="", msg_e="")


@app.route('/login', methods=['POST'])
def loginAdmin():
    ms = ""
    me = ""
    form = AdminLoginForm()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if form.validate_on_submit():
        userName = form.userName.data
        passa = form.password.data
        password = hashlib.sha256(passa.encode()).hexdigest()
        try:
            if cursor.execute('''SELECT * FROM `admin` WHERE user_name=%s AND password=%s''', (userName, password)):
                data = cursor.fetchall()
                session['logged_in'] = True
                return redirect(url_for('addUser'))
            else:
                me = "Invalid credentials Try Again !"
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            me = "Failed to login, Try Again !"
        finally:
            mysql.connection.commit()
            cursor.close()
    return render_template('login.html', form=form, msg_s=ms, msg_e=me)


@app.route('/home/addStudent', methods=['GET'])
@login_required
def dc():
    form = AddStudentForm()
    return render_template('addStudent.html', form=form, msg_s="", msg_e="")


@app.route('/home/addStudent', methods=['POST'])
@login_required
def addStudent():
    form = AddStudentForm()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    ms = ""
    me = ""
    if form.validate_on_submit():
        courseid = form.courseid.data
        studentid = form.studentid.data
        studentname = form.studentname.data
        studentbranch = form.studentbranch.data
        studentsection = form.studentsection.data
        studentyear = form.studentyear.data
        studentimage = base64.b64encode(form.studentimage.data.read())
        try:
            if cursor.execute('''INSERT INTO `students` VALUES(NULL, %s, %s, %s, %s, %s, %s, %s)''', (
                    courseid, studentid, studentname, studentbranch, studentyear, studentsection, studentimage)):
                form.courseid.data = ""
                form.studentid.data = ""
                form.studentname.data = ""
                form.studentbranch.data = ""
                form.studentsection.data = ""
                form.studentyear.data = ""
                ms = "Added Student Successfully"
            else:
                me = "Failed to add student"
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            me = e
        finally:
            mysql.connection.commit()
            cursor.close()
    else:
        me = "Not Validated"
    return render_template('addStudent.html', form=form, msg_s=ms, msg_e=me)


# attendance
@app.route('/home/attendance', methods=['GET', 'POST'])
@login_required
def attendancePage():
    form = my_forms.attendanceForm()
    data = {}
    if form.validate_on_submit():
        class_id = form.classid.data
        date = form.date.data
        date = str(datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y"))
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if cursor.execute("SELECT * FROM `attendance` WHERE class_id=%s AND date=%s", (class_id, date)):
            data = cursor.fetchall()
            return render_template('attendance.html', form=form, msg_e="", data=data)
        else:
            return render_template('attendance.html', form=form, msg_e="No Attendance data for: "+date, data=data)
    return render_template('attendance.html', form=form, msg_e="", data=data)


# api
# login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data['user_id']
    password = (hashlib.sha256(data['password'].encode())).hexdigest()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        if cursor.execute('''SELECT * FROM `users` WHERE user_id = %s AND password = %s''', (user_id, password)):
            data = cursor.fetchall()
            msg = {"status": 1, "message": "Successfully logged in!", "user_name": data[0]['username']}
        else:
            msg = {"status": 0, "message": "Wrong Password or User ID!", "user_name": ""}
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        msg = {"status": 1, "message": e}
    finally:
        mysql.connection.commit()
        cursor.close()
    return msg


# get all TT
@app.route("/api/courses/<userid>", methods=['GET'])
def getCourses(userid):
    user_id = userid
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        if cursor.execute('''SELECT DISTINCT course_id,sec,branch,sem,subj,year FROM time_table WHERE user_id=''' +
                          user_id):
            data = cursor.fetchall()
            msg = {"status": 1, "data": data, "message": "Success"}
        else:
            msg = {"status": 1, "data": [{}], "message": "Success"}
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        msg = {"status": 1, "data": [{}], "message": e}
    return make_response(msg)


# get Time-Table
@app.route("/api/timetable/<userid>", methods=['GET'])
def getTimeTable(userid):
    user_id = userid
    day = getDay()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        if cursor.execute('''SELECT * FROM `time_table` WHERE user_id = %s AND day = %s''', (user_id, day)):
            data = cursor.fetchall()
            msg = {"status": 1, "data": data, "message": "Success"}
        else:
            msg = {"status": 0, "data": [{}], "message": "Failed"}
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        msg = {"status": 1, "data": [{}], "message": e}
    finally:
        mysql.connection.commit()
        cursor.close()
    return make_response(jsonify(msg))


# Attendance
@app.route("/api/attendancehistory", methods=['POST'])
def getAttendanceHistory():
    data = request.get_json()
    time_id = data['id']
    class_id = data['class_id']
    date = data['date']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        if cursor.execute('''SELECT * FROM `attendance` WHERE time_id = %s AND class_id = %s AND date = %s''',
                          (time_id, class_id, date)):
            data = cursor.fetchall()
            msg = {"status": 1, "data": data, "message": "Success"}
        else:
            msg = {"status": 0, "data": [], "message": "Failed"}
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        msg = {"status": 1, "data": [], "message": e}
    finally:
        mysql.connection.commit()
        cursor.close()
    return make_response(jsonify(msg))


class Attendance(Resource):
    task_post_args = reqparse.RequestParser()
    task_post_args.add_argument("class_id", type=str, help="UserName is required!", required=True)
    task_post_args.add_argument("date", type=str, help="Password is required!", required=True)
    task_post_args.add_argument("time", type=str, help="Password is required!", required=True)
    task_post_args.add_argument("subject", type=str, help="Password is required!", required=True)
    task_post_args.add_argument("course_faculty", type=str, help="Password is required!", required=True)

    def post(self):
        time_id = str(request.json['id'])
        class_id = str(request.json['class_id'])
        date = str(request.json['date'])
        time = str(request.json['time'])
        subject = str(request.json['subject'])
        course_faculty = str(request.json['course_faculty'])
        students_list = request.json['students_list']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        status = 0
        for student in students_list:
            student_status = student['student_status']
            if cursor.execute('''SELECT * FROM `attendance` WHERE time_id=%s AND date=%s AND student_id=%s''',
                              (time_id, date, student['student_id'])):
                check = cursor.fetchall()
                if cursor.execute('''UPDATE `attendance` SET time=%s, student_status=%s WHERE time_id=%s AND date=%s AND
                 student_id=%s''', (time, student_status, time_id, date, student['student_id'])):
                    message = "Updated"
                    status = 1
                else:
                    message = "Failed to Update"
                    status = 0
            else:
                if cursor.execute('''INSERT INTO `attendance`(`id`, `time_id`, `date`, `time`, `class_id`, `subject`, `course_faculty`, `student_id`,
                `student_name`, `student_branch`, `student_section`, `student_image`, `student_status`)
                VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %b)''',
                                  (time_id, date, time, class_id, subject,
                                   course_faculty, student['student_id'],
                                   student['student_name'],
                                   student['student_branch'],
                                   student['student_section'],
                                   student['student_image'],
                                   student_status)):
                    message = "Inserted"
                    status = 1
                else:
                    message = "Failed to Insert"
                    status = 0

        mysql.connection.commit()
        cursor.close()
        msg = {"status": status, "message": message}
        return make_response(jsonify(msg))


# compare faces
class Compare(Resource):
    task_post_args = reqparse.RequestParser()
    task_post_args.add_argument("user_name", type=IMAGES, help="UserName is required!", required=True)

    def post(self):
        resp = []
        targets = []
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        images = request.json['image']
        course_id = str(request.json['course_id'])
        i = 0
        for img in images:
            target = "./uploaded_images/target/" + course_id + str(i) + "_target.jpg"
            file_t = convert_and_save(img, course_id, target)
            targets.append(target)
            i = i + 1
        try:
            if cursor.execute('''SELECT * FROM `students` WHERE course_id ="''' + course_id + '''"'''):
                data = cursor.fetchall()
                msg = {"status": 0, "data": data, "message": "Failed"}
                i = 0
                for user in data:
                    source = "./uploaded_images/source/" + course_id + str(i) + "_source.jpg"
                    file_s = convert_and_save(str(user['student_image']), str(user['student_id']), source)
                    i = i + 1
                    for tt in targets:
                        face = face_comparision.main(source, tt, user['student_id'] + str(getDate()))
                        if face['status']:
                            user['student_image'] = face['cropped']
                            user['student_status'] = 1
                            if user in resp:
                                ind = resp.index(user)
                                resp[ind] = user
                            else:
                                resp.append(user)
                        else:
                            check = False
                            for resin in resp:
                                if user['student_id'] == resin['student_id'] and resin['student_status']:
                                    check = True
                            if not check:
                                user['student_image'] = ""
                                user['student_status'] = 0
                                check = False
                                if user in resp:
                                    ind = resp.index(user)
                                    resp[ind] = user
                                else:
                                    resp.append(user)
                msg = {"status": 1, "data": resp, "message": "Success"}
            else:
                msg = {"status": 0, "data": [{}], "message": "Failed"}
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            msg = {"status": 0, "data": [{}], "message": e}
        finally:
            mysql.connection.commit()
            cursor.close()
        return make_response(jsonify(msg))


api.add_resource(Compare, '/api/comparefaces')
api.add_resource(Attendance, '/api/attendance')


def convert_and_save(b64_string, course_id, ty):
    path = ty
    print(b64_string, file=sys.stdout)
    with open(path, "wb") as fh:
        fh.write(base64.decodebytes(b64_string.encode()))
        return fh


#######################
# get geo timezone
def getDay():
    now = datetime.now(pytz.timezone('Etc/GMT+5'))  # you could pass `timezone` object here
    weekday = now.weekday()
    return calendar.day_name[weekday]


def getDate():
    now = datetime.now(pytz.timezone('Etc/GMT+5'))  # you could pass `timezone` object here
    date = now.date()
    return date


if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=5000)
    serve(app, port=5000)
