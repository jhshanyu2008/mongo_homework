from bottle import route, run, template


@route('/hello/<name>')
def index(name):
    return template("<b>Hello {{name}},I'm bottle</b>", name=name)


run(host='Localhost', port=8001)
