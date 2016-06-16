# -*- coding: UTF-8 -*-
from flask import Flask, request, session, redirect, url_for, render_template, flash
from passlib.hash import bcrypt
from datetime import datetime
from models import app, User, Task, FAQ, Notification, get_recent_tasks, get_recent_notifications, get_faqs
from werkzeug import secure_filename

import os
import re

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    user_id = session.get('user_id')
    if user_id:
        user = User.find_by_id(user_id)
        tasks = User.retrieve_feed(user_id)
        return render_template('index.html',  tasks = tasks, user_name=user[1], user_portrait_url = user[6])
    else:
        tasks = get_recent_tasks()
        return render_template('index.html', tasks = tasks)

@app.route('/recent_tasks')
def recent_tasks():
    if session.get('user_id'):
        tasks = get_recent_tasks(session.get('user_id'))
        return render_template('recent_tasks.html', tasks = tasks)
    else:
        return redirect(url_for('index'))

@app.route('/hot_tasks')
def hot_posts():
    if session.get('user_id'):
        posts = get_hot_tasks(session.get('user_id'))
        return render_template('hot_posts.html', posts = posts)
    else:
        return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user_name = request.form['user_name']
        phone_number = request.form['phone_number']
        password = request.form['password']
        campus_address = request.form['campus_address']
        student_id = request.form['student_id']
        portrait = '../static/portraits/default_portrait.jpg'

        if not re.match("^((13[0-9])|(15[^4,\\D])|(18[0,5-9]))\\d{8}$", phone_number):
            flash('手机号码格式不正确','danger')
        elif len(password) < 6:
            flash('密码长度须大于等于6', 'danger')
        elif len(user_name) < 1:
            flash('昵称不能为空', 'danger')
        elif not User.register(user_name, phone_number, password, campus_address, student_id, portrait):
            flash('该邮箱已被用于注册', 'danger')
        else:
            user = User.find_by_phone_number(phone_number)
            session['user_id'] = user[0]
            flash('成功登陆', 'success')
            return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['POST'])
def login():
    phone_number = request.form['phone_number']
    password = request.form['password']

    if not User.verify_password(phone_number, password):
        flash('错误的邮箱或密码','danger')
    else:
        user = User.find_by_phone_number(phone_number)
        session['user_id'] = user[0]
        flash('成功登陆', 'success')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('成功登出', 'success')
    return redirect(url_for('index'))

@app.route('/follow/<target_id>')
def follow(target_id):
    self_id = session.get('user_id')
    target = User.find_by_id(target_id)
    tasks = User.retrieve_published_tasks(target_id)
    if self_id and target:
        User.follow_user(self_id, target_id)
        return redirect(url_for('show_user', user_id=target_id))
    return redirect(url_for('index'))


@app.route('/unfollow/<target_id>')
def unfollow(target_id):
    self_id = session.get('user_id')
    target = User.find_by_id(target_id)
    tasks = User.retrieve_published_tasks(target_id)
    if self_id and target:
        User.unfollow_user(self_id, target_id)
        return redirect(url_for('show_user', user_id=target_id))
    return redirect(url_for('index'))

@app.route('/followingList/<user_id>')
def fetch_following(user_id):
    self_id = session.get('user_id')
    followings = User.find_following(user_id, self_id)
    user = User.find_by_id(user_id)
    return render_template('following.html', followings=followings, user=user)

@app.route('/followerList/<user_id>')
def fetch_follower(user_id):
    self_id = session.get('user_id')
    followers = User.find_follower(user_id, self_id)
    user = User.find_by_id(user_id)
    return render_template('follower.html', followers=followers, user=user)

@app.route('/change_portrait/', methods=['POST'])
def change_portrait():
    user_id = session.get('user_id')
    if user_id:
        portrait = request.files['new_portrait']
        if portrait and allowed_file(portrait.filename):
            fname = secure_filename(portrait.filename) #获取一个安全的文件名，且仅仅支持ascii字符；
            portrait.save(os.path.join(app.config['UPLOAD_FOLDER'], fname)) # From http://flask.pocoo.org/docs/0.10/patterns/fileuploads/#uploading-files
            User.change_portrait(user_id, '../static/portraits/' + fname)

            flash('成功修改头像', 'success')
            return redirect(url_for('show_user', user_id=user_id))

    return redirect(url_for('index'))

@app.route('/add_task', methods=['POST'])
def add_task():
    user_id = session.get('user_id')
    if user_id:
        task_type = request.form['type']
        title = request.form['title']
        content = request.form['content']
        due = {}
        due['year'] = request.form['year']
        due['month'] = request.form['month']
        due['day'] = request.form['day']
        if not title or len (title) == 0 or not content or len(content) == 0:
            flash('任务标题与内容均不能为空','danger')
        else:
            content = transform_mention_text(content, user_id)
            User.add_task(task_type, title, content, due, user_id)
            
            flash('成功发布', 'success')
            return redirect(url_for('show_user', user_id=user_id))

    return redirect(url_for('index'))

@app.route('/task/<task_id>', methods=['GET'])
def show_task(task_id):
    # Check login status
    task = Task.find_by_id(task_id)
    # Search all the comments related.
    adopter = Task.retrieve_adopter(task_id)

    if task:
        self_id = session.get('user_id')
        if self_id:
            if adopter != None:
                me_adopt = (adopter[8] == self_id)
            else:
                me_adopt = False
        else:
            me_adopt = False

        publisher = Task.retrieve_publisher(task_id)
        return render_template('task_page.html', task=task, publisher=publisher, adopter=adopter, me_adopt=me_adopt)
    else:
        return redirect(url_for('index'))

@app.route('/show_notification', methods=['GET'])
def show_notification():
    notifications = Notification.find_all()
    present_datetime = datetime.now()
    return render_template('notification_page.html', notifications = notifications, present_datetime = present_datetime)

@app.route('/show_faq', methods=['GET'])
def show_faq():
    faqs = FAQ.find_all()
    return render_template('FAQ_page.html', faqs = faqs)

@app.route('/users/<user_id>', methods=['GET'])
def all_users(user_id):
    self_id = session.get('user_id')
    all_users = User.find_all_users(user_id)
    return render_template('all_users.html', all_users=all_users)

@app.route('/user/<user_id>', methods=['GET'])
def show_user(user_id):
    self_id = session.get('user_id')
    user = User.find_by_id(user_id)
    friends_2_hop = User.retrieve_2_hop_friends(user_id)
    user_follower_count = User.fetch_follower_count(user_id)
    user_following_count = User.fetch_following_count(user_id)
    score_as_helper = User.fetch_score_as_helper(user_id)
    score_as_helpee = User.fetch_score_as_helpee(user_id)
    if user:
        if self_id:
            tasks = User.retrieve_published_tasks(user_id, self_id)
            adopted_tasks = User.retrieve_adopted_tasks(user_id, self_id)
            if User.is_following(self_id, user_id):
                return render_template('user_page.html', user_name=user[1], tasks=tasks, user_id=user_id, is_following = True, adopted_tasks=adopted_tasks, user_portrait_url = user[6], user_following_count=user_following_count, user_follower_count = user_follower_count, score_as_helper = score_as_helper[0], score_as_helpee = score_as_helpee[0])
            else:
                return render_template('user_page.html', user_name=user[1], tasks=tasks, user_id=user_id, is_following = False, friends_2_hop=friends_2_hop, user_portrait_url = user[6], user_following_count=user_following_count, user_follower_count = user_follower_count, score_as_helper = score_as_helper[0], score_as_helpee = score_as_helpee[0])
        else:
            tasks = User.retrieve_published_tasks(user_id)
            return render_template('user_page.html', user_name=user[1], tasks=tasks, user_id=user_id, user_portrait_url = user[6], user_following_count=user_following_count, user_follower_count = user_follower_count, score_as_helper = score_as_helper[0], score_as_helpee = score_as_helpee[0])
    else:
        return redirect(url_for('index'))

@app.route('/user/<user_id>/profile', methods=['GET'])
def show_user_profile(user_id):
    # Check login status

    return render_template('user_profile_page.html', user_id=user_id)

@app.route('/adopt_task/<task_id>')
def adopt_task(task_id):
    user_id = session.get('user_id')
    if user_id:
        User.adopt_task(user_id, task_id)
    return redirect(url_for('recent_tasks'))
         

@app.route('/unadopt_task/<task_id>')
def unadopt_task(task_id):
    user_id = session.get('user_id')
    if user_id:
        User.unadopt_task(user_id, task_id)
    return redirect(url_for('recent_tasks'))


def transform_mention_text(content, user_id):
    """
    Method for parsing and transforming post content related to mentioning
    @someone  =>   @someone(someone's user ID)
    """
    pattern = re.compile("@[^ ~!#$%^&*?]+")
    mentioned = set(pattern.findall(content))
    mention_mapping = {}
    for user_name in mentioned:
        if "(" in user_name and ")" in user_name:
            continue
        mentioned_user = User.find_by_user_name(user_id, user_name[1:])
        if mentioned_user:
            mention_mapping[user_name] = mentioned_user[0]

    for user_name, real_id in mention_mapping.items():
        content = content.replace(user_name, user_name + "(" + real_id + ")")
    return content
