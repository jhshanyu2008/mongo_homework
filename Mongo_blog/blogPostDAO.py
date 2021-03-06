__author__ = 'aje'

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

import sys
import re
import datetime
import pymongo


# The Blog Post Data Access Object handles interactions with the Posts collection
class BlogPostDAO:

    # constructor for the class
    def __init__(self, database):
        self.db = database
        self.posts = database.posts
        self.post_count = self.posts.count()

    # inserts the blog entry and returns a permalink for the entry
    def insert_entry(self, title, post, tags_array, author):
        print "Inserting a Blog Entry", author, title

        self.post_count += 1
        exp = re.compile('\W')  # match anything not alphanumeric
        whitespace = re.compile('\s')
        temp_title = whitespace.sub("_", title)
        permalink = str(self.post_count) + '_' + exp.sub('', repr(temp_title))

        # Build a new post
        post = {"title": title,
                "author": author,
                "body": post,
                "permalink": permalink,
                "tags": tags_array,
                "comments": [],
                "date": datetime.datetime.utcnow()}

        # now insert the post
        try:
            self.posts.insert_one(post)
            print "Inserted the Post Successfully.", title
        except:
            print "Error inserting post"
            print "Unexpected error:", sys.exc_info()[0]

        return permalink

    # update a blog entry and returns its permalink
    def update_entry(self, permalink, new_title, new_post, new_tag_list):

        print "Updating a Blog Entry", permalink

        # update the post
        try:
            content = {"title": new_title,
                       "body": new_post,
                       "tags": new_tag_list,
                       "date": datetime.datetime.utcnow()}
            result = self.posts.update_one({'permalink': permalink},
                                           {'$set': content})
            print "num matched: ", result.matched_count
            print "Update the Post Successfully.", permalink
        except:
            print "Error updating post"
            print "Unexpected error:", sys.exc_info()[0]

    # returns an array of num_posts posts, reverse ordered by date.
    def get_posts(self, num_posts):

        posts = self.posts.find().sort('date', pymongo.DESCENDING).limit(num_posts)
        post_list = []

        for post in posts:
            post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")  # fix up date
            if 'tags' not in post:
                post['tags'] = []  # fill it in if its not there already
            if 'comments' not in post:
                post['comments'] = []

            post_list.append({'title': post['title'], 'body': post['body'], 'post_date': post['date'],
                              'permalink': post['permalink'],
                              'tags': post['tags'],
                              'author': post['author'],
                              'comments': post['comments']})

        return post_list

    # returns an array of num_posts posts, reverse ordered, filtered by tag
    def get_posts_by_tag(self, tag, num_posts):

        cursor = self.posts.find({'tags': tag}).sort('date', pymongo.DESCENDING).limit(num_posts)
        post_list = []

        for post in cursor:
            post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")  # fix up date
            if 'tags' not in post:
                post['tags'] = []  # fill it in if its not there already
            if 'comments' not in post:
                post['comments'] = []

            post_list.append({'title': post['title'], 'body': post['body'], 'post_date': post['date'],
                              'permalink': post['permalink'],
                              'tags': post['tags'],
                              'author': post['author'],
                              'comments': post['comments']})

        return post_list

    # returns an array of num_posts posts, reverse ordered, filtered by author
    def get_posts_by_author(self, author):
        cursor = self.posts.find({'author': author}).sort('date', pymongo.DESCENDING)
        post_list = []

        for post in cursor:
            post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")  # fix up date
            if 'tags' not in post:
                post['tags'] = []  # fill it in if its not there already
            if 'comments' not in post:
                post['comments'] = []

            post_list.append({'title': post['title'], 'body': post['body'], 'post_date': post['date'],
                              'permalink': post['permalink'],
                              'tags': post['tags'],
                              'author': post['author'],
                              'comments': post['comments']})
        return post_list

    # find a post corresponding to a particular permalink
    def get_post_by_permalink(self, permalink):

        post = None

        try:
            cursor = {"permalink": permalink}
            post = self.posts.find_one(cursor)
        except:
            print "No such post, internal error."

        if post is not None:
            # fix up date
            post['date'] = post['date'].strftime("%A, %B %d %Y at %I:%M%p")

        return post

    # add a comment to a particular blog post
    def add_comment(self, permalink, name, email, body):

        comment = {'author': name, 'body': body, 'date': datetime.datetime.utcnow()}

        if email != "":
            comment['email'] = email

        try:
            result = self.posts.update_one({'permalink': permalink}, {'$push': {'comments': comment}})

            return result.matched_count

        except:
            print "Could not update the collection, error"
            print "Unexpected error:", sys.exc_info()[0]
            return 0
