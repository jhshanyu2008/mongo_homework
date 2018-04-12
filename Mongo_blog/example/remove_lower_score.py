import pymongo

connection = pymongo.MongoClient("mongodb://localhost")

# get a handle to the school database
db = connection.school
students = db.students


def find():
    query = {}  # we need to modify every student,so here set with blank

    cursor = students.find(query)
    for student in cursor:
        scores = student["scores"]
        _id = student["_id"]

        lower_score = 100
        index = None
        homework_count = 0
        for idx in range(len(scores)):
            if scores[idx]["type"] == "homework":
                homework_count += 1
                if scores[idx]["score"] < lower_score:
                    index = idx
                    lower_score = scores[idx]["score"]
        if homework_count <= 1:
            index = None
        try:
            del scores[index]
        except TypeError:
            print "This student does not need to delete homework score, id is {0}".format(_id)

        students.update_one({'_id': _id},
                          {'$set': {'scores': scores}})


if __name__ == '__main__':
    find()
