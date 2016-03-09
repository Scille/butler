from twisted.internet import defer
from autobahn.wamp.exception import ApplicationError
from autobahn.twisted.wamp import ApplicationSession

app = {}
app._start = {}
app._waiting = {}
app._new_app = False


def _start_app(application_name, version):
    global app
    app._start[application_name] = version
    if application_name in app._waiting:
        app._waiting[application_name]['defer'].callback()
    for key in app._waiting:
        if key not in app._start:
            application = app._waiting[key]
            _try_to_start_app(
                application['name'], application['version'], application['required_components'])
    return True


def _add_to_waiting_list(application_name, version, required_components):
    global app

    if application_name in app._waiting:
        del app._waiting[application_name]
    app._waiting[application_name] = {
        'name': application_name, 'version': version, 'required_components': required_components, 'defer': None}
    return False


def _try_to_start_app(application_name, version, required_components):
    global app
    if not required_components:
        return _start_app(application_name, version)
    else:
        start_component = []
        for key in required_components.keys():
            if key in app._start and required_components[key] == app._start[key]:
                start_component.append(key)
        if len(start_component) == len(required_components):
            return _start_app(application_name, version)
        else:
            return _add_to_waiting_list(application_name, version, required_components)


class MestrSession(ApplicationSession):

    def onJoin(self, details):
        def authenticate(realm, authid, details):
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

             when all the different component required has been register your component will
             be allow to authenticate with a role build only for your application with
             only the right right for it to works
             """

            global app
            ticket = details['ticket']
            if 'application_name' not in ticket and 'version' not in ticket:
                raise ApplicationError(
                    'could not start the authentication of an app, field application_name or version is missing')
            application_name = ticket['application_name']
            version = ticket['version']
            required_components = ticket[
                'required_components'] if 'required_components' in ticket else {}
            if not _try_to_start_app(application_name, version, required_components):
                ready_defered = defer.Deferred()
                ready_defered.addCallback(_try_to_start_app,
                                          application_name=application_name,
                                          version=version,
                                          required_components=required_components)
                app._waiting[application_name]['defer'] = ready_defered
                yield ready_defered

            for k in app._start:
                if k in app._waiting:
                    del app._waiting[k]

            # fake role for the moment must be contains in the ticket
            return ticket['role']

        return self.register(authenticate, 'mestr.authenticate')
