# -*- coding: utf-8 -*-
from flask import Flask
from flask.ext.mysql import MySQL
from passlib.hash import bcrypt
from datetime import datetime
import os
import uuid
import string

mysql = MySQL()

app = Flask(__name__)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_DB'] = 'helpingsys'

UPLOAD_FOLDER = app.root_path + '/static/portraits'
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'root'
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_PORT'] = 3306
# app.config['MYSQL_DB'] = 'helpingsys'

mysql.init_app(app)


class User:

    def __init__(self, user_id):
        self.user_id = user_id


    @classmethod
    def find_by_phone_number(cls, user_phone_number):
        query = """
        SELECT *
        FROM User
        WHERE phone_number = %s;
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_phone_number, ))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user

    @classmethod
    def find_by_id(cls, user_id):
        query = """
        SELECT *
        FROM User
        WHERE user_id = %s;
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user

    @classmethod
    def find_by_user_name(cls, user_id, user_name):
        query = """
        SELECT User.user_id
        FROM Follow, User
        WHERE Follow.source_id = %s AND Follow.target_id = User.user_id AND User.user_name = %s;
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, user_name))
        user = cursor.fetchall()
        cursor.close()
        connection.close()
        return user

    @classmethod
    def find_all_users(cls, user_id):
        query = """
        SELECT *
        FROM User LEFT OUTER JOIN (SELECT F2.target_id, count(*)
                                   FROM Follow as F1 INNER JOIN Follow as F2
                                   ON F1.source_id = F2.target_id
                                   WHERE F1.target_id = %s AND F2.source_id = F1.target_id
                                   GROUP BY F2.target_id) as A
        ON User.user_id = A.target_id
        ORDER BY User.user_name ASC LIMIT 25
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        user = cursor.fetchall()
        cursor.close()
        connection.close()
        return user

    @classmethod
    def register(cls, user_name, phone_number, password, campus_address, student_id, portrait):
        if not User.find_by_phone_number(phone_number):
            query = """
            INSERT INTO User
            (`user_id`,
            `user_name`,
            `phone_number`,
            `password`,
            `campus_address`,
            `student_id`,
            `portrait`)
            VALUES
            (%s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s);
            """
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(query, (uuid.uuid4(), user_name, phone_number, bcrypt.encrypt(password), campus_address, student_id, portrait))
            connection.commit()
            cursor.close()
            connection.close()
            return True
        else:
            return False
    
    @classmethod
    def verify_password(cls, phone_number, password):
        user = User.find_by_phone_number(phone_number)
        if user:
            return bcrypt.verify(password, user[3])
        else:
            return False

    @classmethod
    def change_portrait(cls, user_id, fname):
        query = """
        UPDATE User
        SET portrait = %s
        WHERE user_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (fname, user_id))
        connection.commit()
        cursor.close()
        connection.close()

    @classmethod
    def find_following(cls, user_id, self_id):
        query = """
        SELECT *
        FROM User INNER JOIN (SELECT target_id, COUNT(*) AS FOLLOWING
                              FROM Follow
                              WHERE source_id = %s OR source_id = %s
                              GROUP BY target_id) as F
        ON User.user_id = F.target_id
        ORDER BY user_name ASC LIMIT 25;
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, self_id))
        following = cursor.fetchall()
        cursor.close()
        connection.close()
        return following

    @classmethod
    def find_follower(cls, user_id, self_id):
        query = """
        SELECT *
        FROM User LEFT OUTER JOIN (SELECT F2.target_id, count(*)
                                   FROM Follow as F1 INNER JOIN Follow as F2
                                   ON F1.source_id = F2.target_id
                                   WHERE F1.target_id = %s AND F2.source_id = F1.target_id
                                   GROUP BY F2.target_id) as A
        ON User.user_id = A.target_id
        ORDER BY User.user_name ASC LIMIT 25
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        follower = cursor.fetchall()
        cursor.close()
        connection.close()
        return follower

    @classmethod
    def add_task(cls, task_type, title, description, due, publisher):
        query = """
        INSERT INTO Task
        (`task_id`,
        `task_type`,
        `task_title`,
        `task_description`,
        `due`,
        `publisher`,
        `publish_timestamp`,
        `publish_date`,
        `status`,
        `helper_score`,
        `helpee_score`)
        VALUES
        (%s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s);
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (uuid.uuid4(), task_type, title, description, date2str(due['year'], due['month'], due['day']), publisher, date(), date(), "PUBLISHED", 4, 4))
        connection.commit()
        cursor.close()
        connection.close()

    @classmethod
    def post_notification(cls, noti_title, noti_content, noti_expire_date):
        query = """
        INSERT INTO Notification
        (`noti_id`,
        `noti_title`,
        `noti_content`,
        `noti_publish_time`,
        `noti_expire_date`)
        VALUES
        (%s,
        %s,
        %s,
        %s,
        %s)
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (uuid.uuid4(), noti_title, noti_content, timestamp(), noti_expire_date))
        connection.commit()
        cursor.close()
        connection.close()

    @classmethod
    def post_FAQ(cls, question_content, answer_content):
        query = """
        INSERT INTO FAQ
        (`faq_id`,
        `question_content`,
        `answer_content`)
        VALUES
        (%s,
        %s,
        %s)
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (uuid.uuid4(), question_content, answer_content))
        connection.commit()
        cursor.close()
        connection.close()

    @classmethod
    def adopt_task(cls, user_id, task_id):
        query = """
        UPDATE Task
        SET adopter = %s, status = "ADOPTED", adopt_timestamp = %s, adopt_date = %s
        WHERE task_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, datetime.now(), datetime.now(), task_id))
        connection.commit()
        cursor.close()
        connection.close()

    @classmethod
    def unadopt_task(cls, user_id, task_id):
        query = """
        UPDATE Task
        SET adopter = NULL, status = "PUBLISHED", adopt_timestamp = NULL, adopt_date = NULL
        WHERE task_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        rel = cursor.execute(query, (task_id, ))
        connection.commit()
        cursor.close()
        connection.close()

    @classmethod
    def helper_commit_job(cls, task_id):
        query = """
        UPDATE Task
        SET status = "DONE"
        WHERE task_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (task_id, ))
        connection.commit()
        cursor.close()
        connection.close()

    @classmethod
    def helper_assess(cls, task_id, helpee_score):
        query = """
        UPDATE Task
        SET helpee_score = %s
        WHERE task_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (helpee_score, task_id))
        connection.commit()
        cursor.close()
        connection.close()

    @classmethod
    def helpee_assess(cls, task_id, helper_score):
        query = """
        UPDATE Task
        SET helper_score = %s, status = "CHECKED"
        WHERE task_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (helper_score, task_id))
        connection.commit()
        cursor.close()
        connection.close()
    
    @classmethod
    def fetch_published_tasks(cls, user_id):
        query_helpee = """
        SELECT *
        FROM Task
        WHERE publisher = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        published_tasks = cursor.fetchall()
        cursor.close()
        connection.close()
        return published_tasks

    @classmethod
    def calculate_helper_score(cls, user_id):
        query = """
        SELECT AVERAGE(helper_score)
        FROM Task
        WHERE adopter = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        helper_score = cursor.fetchone()
        cursor.close()
        connection.close()
        return helper_score

    @classmethod
    def calculate_helpee_score(cls, user_id):
        query = """
        SELECT AVERAGE(helpee_score)
        FROM Task
        WHERE publisher = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id))
        helpee_score = cursor.fetchone()
        cursor.close()
        connection.close()
        return helpee_score

    @classmethod
    def follow_user(cls, source_id, target_id):
        query = """
        INSERT Follow
        (`source_id`,
        `target_id`)
        VALUES
        (%s,
        %s)
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (source_id, target_id))
        connection.commit()
        cursor.close()
        connection.close()

    @classmethod
    def unfollow_user(cls, source_id, target_id):
        query = """
        DELETE
        FROM Follow
        WHERE source_id = %s AND target_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (source_id, target_id))
        connection.commit()
        cursor.close()
        connection.close()
        
    @classmethod
    def is_following(cls, source_id, target_id):
        query = """
        SELECT *
        FROM Follow
        WHERE source_id = %s AND target_id = %s
        LIMIT 1
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (source_id, target_id))
        is_following = cursor.fetchone()
        cursor.close()
        connection.close()
        return is_following != None

    @classmethod
    def retrieve_adopted_tasks(cls, user_id, self_id = None):
        if self_id:
            query = """
            SELECT *
            FROM Task INNER JOIN User
            ON Task.publisher = User.user_id
            WHERE adopter = %s OR adopter = %s
            ORDER BY adopt_timestamp DESC LIMIT 3
            """
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(query, (user_id, self_id))
            adopted_tasks = cursor.fetchall()
            cursor.close()
            connection.close()
            return adopted_tasks
            
        else:
            query = """
            SELECT *
            FROM Task
            WHERE adopter = %s
            ORDER BY adopt_timestamp DESC LIMIT 3
            """
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(query, (user_id, ))
            adopted_tasks = cursor.fetchall()
            cursor.close()
            connection.close()
            return adopted_tasks
            
    @classmethod
    def retrieve_published_tasks(cls, user_id, self_id = None):
        if self_id:
            query = """
            SELECT *
            FROM Task INNER JOIN User
            ON Task.publisher = User.user_id
            WHERE Task.publisher = %s OR Task.publisher = %s
            ORDER BY publish_timestamp DESC LIMIT 25
            """
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(query, (user_id, self_id))
            published_tasks = cursor.fetchall()
            cursor.close()
            connection.close()
            return published_tasks
            
        else:
            query = """
            SELECT *
            FROM Task INNER JOIN User
            ON Task.publisher = User.user_id
            WHERE publisher = %s
            ORDER BY publish_timestamp DESC LIMIT 25
            """
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(query, (user_id, ))
            published_tasks = cursor.fetchall()
            cursor.close()
            connection.close()
            return published_tasks

    @classmethod
    def retrieve_feed(cls, user_id):
        query = """
        SELECT *
        FROM Task INNER JOIN User
        ON Task.publisher = User.user_id
        WHERE Task.publisher IN (SELECT target_id
                                FROM Follow
                                WHERE source_id = %s)
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        feed = cursor.fetchall()
        cursor.close()
        connection.close()
        return feed

    @classmethod
    def retrieve_2_hop_friends(cls, user_id):
        query = """
        SELECT u3.user_id, u3.user_name, u3.portrait
        FROM Follow f1, User u2, Follow f2, User u3
        WHERE f1.source_id = %s AND u2.user_id = f1.target_id AND f2.source_id = u2.user_id AND u3.user_id = f2.target_id
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        friends_2_hop = cursor.fetchall()
        cursor.close()
        connection.close()
        return friends_2_hop

    @classmethod
    def fetch_follower_count(cls, user_id):
        query = """
        SELECT COUNT(DISTINCT Task.task_id), COUNT(DISTINCT Follow.source_id)
        FROM Task LEFT OUTER JOIN Follow
        ON Follow.target_id = Task.publisher
        WHERE Task.publisher = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        self_info = cursor.fetchone()
        cursor.close()
        connection.close()
        return self_info

    @classmethod
    def fetch_following_count(cls, user_id):
        query = """
        SELECT COUNT(DISTINCT Task.task_id), COUNT(DISTINCT Follow.target_id)
        FROM Task LEFT OUTER JOIN Follow
        ON Follow.source_id = Task.publisher
        WHERE Task.publisher = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        self_info = cursor.fetchone()
        cursor.close()
        connection.close()
        return self_info

    @classmethod
    def fetch_score_as_helper(cls, user_id):
        query = """
        SELECT AVG(helper_score)
        FROM Task
        WHERE adopter = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        helper_score = cursor.fetchone()
        cursor.close()
        connection.close()
        return helper_score

    @classmethod
    def fetch_score_as_helpee(cls, user_id):
        query = """
        SELECT AVG(helpee_score)
        FROM Task
        WHERE publisher = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, ))
        helpee_score = cursor.fetchone()
        cursor.close()
        connection.close()
        return helpee_score

class Task:
    @classmethod
    def find_by_id(cls, task_id):
        query = """
        SELECT *
        FROM Task
        WHERE task_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (task_id, ))
        task = cursor.fetchone()
        cursor.close()
        connection.close()
        return task

    @classmethod
    def retrieve_content(cls, task_id):
        query = """
        SELECT description
        FROM Task
        WHERE task_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (task_id, ))
        content = cursor.fetchone()
        cursor.close()
        connection.close()
        return content

    @classmethod
    def count_adopt(cls, task_id):
        query = 'OPTIONAL MATCH ()-[r:LIKED]->(:Task {id:{task_id}}) RETURN COUNT(r)'
        return graph.cypher.execute(query, task_id=task_id).one

    @classmethod
    def retrieve_adopter(cls, task_id):
        query = """
        SELECT *
        FROM Task INNER JOIN User
        ON Task.adopter = User.user_id
        WHERE task_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (task_id, ))
        adopter = cursor.fetchone()
        cursor.close()
        connection.close()
        return adopter

    @classmethod
    def retrieve_publisher(cls, task_id):
        query = """
        SELECT publisher
        FROM Task
        WHERE task_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (task_id, ))
        publisher = cursor.fetchone()
        cursor.close()
        connection.close()
        return publisher

class Notification:
    @classmethod
    def find_by_id(cls, noti_id):
        query = """
        SELECT *
        FROM Notification
        WHERE noti_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (noti_id, ))
        notification = cursor.fetchone()
        cursor.close()
        connection.close()
        return notification

    @classmethod
    def find_all(cls):
        query = """
        SELECT *
        FROM Notification
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query)
        notification = cursor.fetchall()
        cursor.close()
        connection.close()
        return notification

    @classmethod
    def retrieve_content(cls, noti_id):
        query = """
        SELECT content
        FROM Notification
        WHERE noti_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (noti_id, ))
        content = cursor.fetchone()
        cursor.close()
        connection.close()
        return content

    @classmethod
    def retrieve_expire_date(cls, noti_id):
        query = """
        SELECT noti_expire_date
        FROM Notification
        WHERE noti_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (noti_id, ))
        noti_expire_date = cursor.fetchone()
        cursor.close()
        connection.close()
        return noti_expire_date

class FAQ:
    @classmethod
    def find_by_id(cls, faq_id):
        query = """
        SELECT *
        FROM FAQ
        WHERE faq_id = %s
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (faq_id, ))
        faq = cursor.fetchone()
        cursor.close()
        connection.close()
        return faq

    @classmethod
    def find_all(cls):
        query = """
        SELECT *
        FROM FAQ
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query)
        faq = cursor.fetchall()
        cursor.close()
        connection.close()
        return faq

def get_recent_tasks(user_id = None):
    if user_id:
        query = """
        SELECT *
        FROM Task INNER JOIN User
        ON Task.publisher = User.user_id
        WHERE (status = "PUBLISHED" OR adopter = %s) AND due > %s
        ORDER BY publish_date DESC LIMIT 25
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (user_id, date()))
        recent_tasks = cursor.fetchall()
        cursor.close()
        connection.close()

    else:
        query = """
        SELECT *
        FROM Task INNER JOIN User
        ON Task.publisher = User.user_id AND due > %s
        WHERE status = "PUBLISHED"
        ORDER BY publish_timestamp DESC LIMIT 25
        """
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(query, (date(), ))
        recent_tasks = cursor.fetchall()
        cursor.close()
        connection.close()
    
    return recent_tasks


def get_recent_notifications():
    query = """
    SELECT *
    FROM Notification
    ORDER BY noti_publish_time
    """
    connection = mysql.connect()
    cursor = connection.cursor()
    cursor.execute(query)
    recent_notifications = cursor.fetchall()
    cursor.close()
    connection.close()
    return recent_notifications

def get_faqs():
    query = """
    SELECT *
    FROM FAQ
    """
    connection = mysql.connect()
    cursor = connection.cursor()
    cursor.execute(query)
    faqs = cursor.fetchall()
    cursor.close()
    connection.close()
    return faqs

def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

def date():
    return datetime.now().strftime('%Y-%m-%d %H:%M')

def date2str(year, month, day):
    year = string.atoi(year)
    month = string.atoi(month)
    day = string.atoi(day)
    d = datetime(year, month, day)
    return '{:%Y-%m-%d}'.format(d)

def combine(left, right, attrname):
    for l, r in zip(left, right):
        value = getattr(r, attrname)
        setattr(l, attrname, value)

def mysql_fetch_assoc(cursor) :
    data = cursor.fetchone()
    if data == None :
        return None
    desc = cursor.description

    dict = {}

    for (name, value) in zip(desc, data) :
        dict[name[0]] = value

    return dict

def join(task_id, user_id):
    query = """
    SELECT *
    FROM Task
    WHERE task_id = %s
    INNER JOIN
    SELECT *
    FROM User
    WHERE user_id = %s
    ON Task.publisher = User.user_id
    """
    connection = mysql.connect()
    cursor = connection.cursor()
    cursor.execute(query, (task_id, user_id))
    display_tuple = cursor.fetchall()
    cursor.close()
    connection.close()
