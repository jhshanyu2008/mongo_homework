# coding=utf-8
#
# Copyright (c) 2008 - 2013 10gen, Inc. <http://10gen.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
import cgi
import os
import re
import sys

import bottle
import pymongo

import blogPostDAO
import sessionDAO
import userDAO

__author__ = 'aje'


# General Discussion on structure. This program implements a blog. This file is the best place to start to get
# to know the code. In this file, which is the controller, we define a bunch of HTTP routes that are handled
# by functions. The basic way that this magic occurs is through the decorator design pattern. Decorators
# allow you to modify a function, adding code to be executed before and after the function. As a side effect
# the bottle.py decorators also put each callback into a route table.
# These are the routes that the blog must handle. They are decorated using bottle.py
# This route is the main page of the blog


pro_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(pro_path)
css_path = '/'.join((pro_path, 'template/css'))
image_path = '/'.join((pro_path, 'template/images'))
script_path = '/'.join((pro_path, 'template/scripts'))


@bottle.route('/css/<filename:re:.*\.css>')
@bottle.route('/tag/css/<filename:re:.*\.css>')
@bottle.route('/author/css/<filename:re:.*\.css>')
@bottle.route('/post/css/<filename:re:.*\.css>')
def index_static_css(filename):
    """定义静态css资源路径"""
    return bottle.static_file(filename, root=css_path)


@bottle.route('/images/<filename:re:.*\.jpg|.*\.gif|.*\.png>')
@bottle.route('/tag/images/<filename:re:.*\.jpg|.*\.gif|.*\.png>')
@bottle.route('/author/images/<filename:re:.*\.jpg|.*\.gif|.*\.png>')
@bottle.route('/post/images/<filename:re:.*\.jpg|.*\.gif|.*\.png>')
def index_static_image(filename):
    """定义图片资源路径"""
    return bottle.static_file(filename, root=image_path)


@bottle.route('/scripts/<filename:re:.*\.js|.*\.php>')
@bottle.route('/tag/scripts/<filename:re:.*\.js|.*\.php>')
@bottle.route('/author/scripts/<filename:re:.*\.js|.*\.php>')
@bottle.route('/post/scripts/<filename:re:.*\.js|.*\.php>')
def index_static_script(filename):
    """定义js资源路径"""
    return bottle.static_file(filename, root=script_path)


@bottle.route('/')
def blog_index():
    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)

    # even if there is no logged in user, we can show the blog
    post_list = posts.get_posts(15)
    page = "main"

    return bottle.template('template/blog_main.html', dict(myposts=post_list, username=username, page=page))


# The main page of the blog, filtered by tag
@bottle.route('/tag/<tag>')
def posts_by_tag(tag="notfound"):
    cookie = bottle.request.get_cookie("session")
    tag = cgi.escape(tag)

    username = sessions.get_username(cookie)

    print "About to query on tag : ", tag
    # even if there is no logged in user, we can show the blog
    post_list = posts.get_posts_by_tag(tag, 10)
    page = "tag"

    return bottle.template('template/blog_fliter.html', dict(myposts=post_list, username=username, page=page))


# The main page of the blog, filtered by author
@bottle.route('/author/<author>')
def posts_by_tag(author="notfound"):
    cookie = bottle.request.get_cookie("session")
    author = cgi.escape(author)

    username = sessions.get_username(cookie)

    print "About to query on author : ", author
    # even if there is no logged in user, we can show the blog
    post_list = posts.get_posts_by_author(author)
    page = 'author'

    return bottle.template('template/blog_fliter.html', dict(myposts=post_list, username=username, page=page))


# Displays the form allowing a user to add a new post. Only works for logged in users
@bottle.get('/newpost')
def get_newpost():
    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        bottle.redirect("/login")

    return bottle.template("template/blog_newpost.html",
                           dict(subject="", body="", errors="", tags="", username=username))


@bottle.get('/update/<permalink>')
def get_newpost(permalink="notfound"):
    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        bottle.redirect("/login")

    permalink = cgi.escape(permalink)
    post = posts.get_post_by_permalink(permalink)

    if post is None:
        bottle.redirect("/post_not_found")

    newline = re.compile("<p>")
    formatted_post = newline.sub('\r\n', post["body"])

    tag_str = ""
    for tag in post["tags"]:
        tag_str += tag + " "

    return bottle.template("template/blog_updatepost.html",
                           dict(permalink=permalink, subject=post["title"],
                                body=formatted_post, errors="", tags=tag_str, username=username))


# Post handler for setting up a new post.
# Only works for logged in user.
@bottle.post('/newpost')
def post_newpost():
    title = bottle.request.forms.get("subject")
    post = bottle.request.forms.get("body")
    tags = bottle.request.forms.get("tags")

    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        bottle.redirect("/login")

    if title == "" or post == "":
        errors = "Post must contain a title and blog entry"
        return bottle.template("template/blog_newpost.html",
                               dict(subject=cgi.escape(title, quote=True), username=username,
                                    body=cgi.escape(post, quote=True), tags=tags, errors=errors))

    # extract tags
    tags = cgi.escape(tags)
    tags_array = extract_tags(tags)

    # looks like a good entry, insert it escaped
    escaped_post = cgi.escape(post, quote=True)

    # substitute some <p> for the paragraph breaks
    newline = re.compile('\r?\n')
    formatted_post = newline.sub("<p>", escaped_post)

    permalink = posts.insert_entry(title, formatted_post, tags_array, username)

    # now bottle.redirect to the blog permalink
    bottle.redirect("/post/" + permalink)


# Post handler for updating an existed post.
# Only works for logged in user.
@bottle.post('/update/<permalink>')
def post_updatepost(permalink="no found"):
    new_title = bottle.request.forms.get("subject")
    new_post = bottle.request.forms.get("body")
    new_tags = bottle.request.forms.get("tags")

    cookie_sess = bottle.request.get_cookie("session")

    username = sessions.get_username(cookie_sess)  # see if user is logged in
    if username is None:
        bottle.redirect("/login")

    if new_title == "" or new_post == "":
        errors = "Post must contain a title and blog entry"
        return bottle.template("template/blog_updatepost.html",
                               dict(subject=cgi.escape(new_title, quote=True), username=username,
                                    body=cgi.escape(new_post, quote=True), tags=new_tags, errors=errors))

    # extract tags
    new_tags = cgi.escape(new_tags)
    new_tag_list = extract_tags(new_tags)

    # looks like a good entry, insert it escaped
    escaped_post = cgi.escape(new_post, quote=True)

    # substitute some <p> for the paragraph breaks
    newline = re.compile('\r?\n')
    formatted_post = newline.sub("<p>", escaped_post)

    posts.update_entry(permalink, new_title, formatted_post, new_tag_list)

    bottle.redirect("/post/" + permalink)


# Displays a particular blog post
@bottle.get("/post/<permalink>")
def show_post(permalink="notfound"):
    cookie = bottle.request.get_cookie("session")

    username = sessions.get_username(cookie)
    permalink = cgi.escape(permalink)

    print "About to query on permalink : ", permalink
    post = posts.get_post_by_permalink(permalink)

    if post is None:
        bottle.redirect("/post_not_found")

    # init comment form fields for additional comment
    response = {'name': "", 'body': "", 'email': ""}

    return bottle.template("template/blog_entry.html", dict(post=post, username=username, errors="", response=response))


# used to process a comment on a blog post
@bottle.post('/newcomment')
def post_new_comment():
    name = bottle.request.forms.get("responseName")
    email = bottle.request.forms.get("responseEmail")
    body = bottle.request.forms.get("responseBody")
    permalink = bottle.request.forms.get("permalink")

    post = posts.get_post_by_permalink(permalink)
    cookie = bottle.request.get_cookie("session")

    username = sessions.get_username(cookie)

    # if post not found, redirect to post not found error
    if post is None:
        bottle.redirect("/post_not_found")
        return

    # if values not good, redirect to view with errors

    if name == "" or body == "":
        # user did not fill in enough information

        # init comment for web form
        response = {'name': name, 'email': email, 'body': body}

        errors = "Post must contain your name and an actual comment."
        return bottle.template("template/blog_entry.html",
                               dict(post=post, username=username, errors=errors, response=response))

    else:

        # it all looks good, insert the comment into the blog post and redirect back to the post viewer
        posts.add_comment(permalink, name, email, body)

        bottle.redirect("/post/" + permalink)


@bottle.get("/post_not_found")
def post_not_found():
    return "Sorry, post not found"


# displays the initial blog signup form
@bottle.get('/signup')
def present_signup():
    return bottle.template("template/blog_signup.html",
                           dict(username="", password="",
                                password_error="",
                                email="", username_error="", email_error="",
                                verify_error=""))


# displays the initial blog login form
@bottle.get('/login')
def present_login():
    return bottle.template("template/blog_login",
                           dict(username="", password="",
                                login_error=""))


# handles a login request
@bottle.post('/login')
def process_login():
    username = bottle.request.forms.get("username")
    password = bottle.request.forms.get("password")

    print "user submitted ", username, "pass ", password

    user_record = users.validate_login(username, password)
    if user_record:
        # username is stored in the user collection in the _id key
        session_id = sessions.start_session(user_record['_id'])

        if session_id is None:
            bottle.redirect("/internal_error")  # 服务器问题：有效的登陆不可能没有对应的session

        cookie = session_id

        # Warning, if you are running into a problem whereby the cookie being set here is
        # not getting set on the redirect, you are probably using the experimental version of bottle (.12).
        # revert to .11 to solve the problem.
        bottle.response.set_cookie("session", cookie)

        bottle.redirect("/welcome")

    else:
        return bottle.template("template/blog_login.html",
                               dict(username=cgi.escape(username), password="",
                                    login_error="Invalid Login"))


@bottle.get('/internal_error')
@bottle.view('template/blog_error.html')
def present_internal_error():
    return {'error': "System has encountered a DB error"}


@bottle.get('/logout')
def process_logout():
    cookie = bottle.request.get_cookie("session")

    sessions.end_session(cookie)

    bottle.response.set_cookie("session", "")

    bottle.redirect("/signup")


@bottle.post('/signup')  # signup页面的post处理
def process_signup():
    username = bottle.request.forms.get("username")
    password = bottle.request.forms.get("password")
    verify = bottle.request.forms.get("verify")
    email = bottle.request.forms.get("email")

    # set these up in case we have an error case
    # 使用 URL 编码来转义字符串
    errors = {'username': cgi.escape(username), 'email': cgi.escape(email)}
    # 判断输入的值是否合规
    if validate_signup(username, password, verify, email, errors):

        if not users.add_user(username, password, email):
            # this was a duplicate
            errors['username_error'] = "Username already in use. Please choose another"
            return bottle.template("template/blog_signup", errors)

        # 给加密用cookie的
        session_id = sessions.start_session(username)
        print session_id
        bottle.response.set_cookie("session", session_id)
        bottle.redirect("/welcome")  # 重定向到 welcome页面
    else:
        print "user did not validate"
        return bottle.template("template/blog_signup", errors)


@bottle.get("/welcome")
def present_welcome():
    # check for a cookie, if present, then extract value

    cookie = bottle.request.get_cookie("session")
    username = sessions.get_username(cookie)  # see if user is logged in
    if username is None:
        print "welcome: can't identify user...redirecting to signup"
        bottle.redirect("/signup")

    return bottle.template("template/blog_welcome.html", {'username': username})


# Helper Functions

# validates that the user information is valid for new signup, return True of False
# and fills in the error string if there is an issue
def validate_signup(username, password, verify, email, errors):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")  # 只能英文+数字+下划线
    PASS_RE = re.compile(r"^.{3,20}$")  # 只能3-20的长度
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")  # 邮箱地址规则

    errors['username_error'] = ""
    errors['password_error'] = ""
    errors['verify_error'] = ""
    errors['email_error'] = ""

    if not USER_RE.match(username):
        errors['username_error'] = "invalid username. try just letters and numbers"
        return False

    if not PASS_RE.match(password):
        errors['password_error'] = "invalid password."
        return False
    if password != verify:
        errors['verify_error'] = "password must match"
        return False
    if email != "":
        if not EMAIL_RE.match(email):
            errors['email_error'] = "invalid email address"
            return False
    return True


# extracts the tag from the tags form element. an experience python programmer could do this in  fewer lines, no doubt
def extract_tags(tags):

    tags_array = tags.split(' ')

    # let's clean it up
    cleaned = []
    for tag in tags_array:
        if tag not in cleaned and tag != "":
            cleaned.append(tag)

    return cleaned


connection_string = "mongodb://localhost"
connection = pymongo.MongoClient(connection_string)
database = connection.blog

posts = blogPostDAO.BlogPostDAO(database)
users = userDAO.UserDAO(database)
sessions = sessionDAO.SessionDAO(database)

bottle.debug(True)
bottle.run(host='192.168.1.100', port=8082)  # Start the webserver running and wait for requests
