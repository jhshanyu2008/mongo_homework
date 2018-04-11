import bottle
import pymongo


# @bottle.route('/')
# def index():
#     connection = pymongo.MongoClient('localhost', 27017)
#     db = connection.test
#
#     name = db.names
#     item = name.find_one()
#
#     return '<b>Hello %s!</b>' % item['name']


@bottle.route('/')
def home_page():
    mythings = ['apple', 'orange', 'banana', 'peach']
    return bottle.template('template/hello world', username="Shan Yu", things=mythings)


@bottle.post('/favorite_fruit')
def favorite_fruit():
    fruit = bottle.request.forms.get("fruit")
    if fruit is None or fruit == "":
        fruit = "No Fruit Selected"
    bottle.response.set_cookie("fruit", fruit)
    bottle.redirect("/show_fruit")
    # return bottle.template('template/fruit_selected', fruit=fruit)


@bottle.route('/show_fruit')
def show_fruit():
    fruit = bottle.request.get_cookie("fruit")
    return bottle.template('template/fruit_selected', fruit=fruit)


bottle.debug(True)
bottle.run(host='localhost', port=8001)
