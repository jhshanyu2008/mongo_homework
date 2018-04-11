#!/usr/bin/env python
import pymongo

# establish a connection to the database
connection = pymongo.MongoClient("mongodb://localhost")

# get a handle to the school database
db = connection.students
grades = db.grades


def find():
    del_id = []
    print "find, reporting for duty"
    for i in range(200):
        query_student = {'student_id': i, 'type': "homework"}
        cursor = grades.find(query_student)
        cursor.sort([('student_id', pymongo.ASCENDING),
                     ('score', pymongo.ASCENDING)]).limit(1)
        for doc in cursor:
            del_id.append(doc["_id"])

    # for i in range(200):
    #     grades.delete_many({'_id': del_id[i]})

    print "over"




    # try:
    #     cursor = grades.find(query)
    #
    # except Exception as e:
    #     print "Unexpected error:", type(e), e

    # sanity = 0
    # print cursor.count()
    # for doc in cursor:
    #     print doc['student_id'], " ", doc['score']
        # sanity += 1
        # if sanity > 10:
        #     break


if __name__ == '__main__':
    find()
