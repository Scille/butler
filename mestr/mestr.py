from autobahn.twisted.wamp import Application

app = Application("mestr")

app._start = {}
app._waiting = {}


def _start_app(application_name, version):
    global app
    app._start[application_name] = version
    app.session.publish('mestr.' + application_name + '.start')
    for key in app._waiting:
        if key not in app._start:
            application = app._waiting[key]
            _try_to_start_app(
                application['name'], application['version'], application['required_components'])


def _add_to_waiting_list(application_name, version, required_components):
    global app

    if application_name in app._waiting:
        del app._waiting[application_name]
    app._waiting[application_name] = {
        'name': application_name, 'version': version, 'required_components': required_components}


def _try_to_start_app(application_name, version, required_components):
    global app
    if not required_components:
        _start_app(application_name, version)
    else:
        start_component = []
        for key in required_components.keys():
            if key in app._start and required_components[key] == app._start[key]:
                start_component.append(key)
        if len(start_component) == len(required_components):
            _start_app(application_name, version)
        else:
            _add_to_waiting_list(application_name, version, required_components)


@app.register()
def register(application_name, version, required_components=None):
    """
    application_name : name of your application
    version : version of your application
    required_components dictionary of components required for you application
    and their version required

        {
           "component" : "1.1",
           "component2" : "0.1",
           ...
        }

     the mestr will publish an event:

         mestr.your_application_name.start

     when all the different component required has been register
     """
    global app
    _try_to_start_app(application_name, version, required_components)
    for k in app._start:
        if k in app._waiting:
            del app._waiting[k]


if __name__ == '__main__':
    app.run(url="ws://127.0.0.1:8080/ws")
