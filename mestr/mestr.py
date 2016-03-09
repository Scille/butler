from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks
from autobahn.wamp.exception import ApplicationError
from autobahn.twisted.wamp import ApplicationSession

_start = {}
_waiting = {}


def _start_app(application_name, version):
    global _start
    global _waiting
    _start[application_name] = version
    if application_name in _waiting:
        _waiting[application_name]['defer'].callback()
    for key in _waiting:
        if key not in _start:
            application = _waiting[key]
            _try_to_start_app(
                application['name'], application['version'], application['required_components'])
    return True


def _add_to_waiting_list(application_name, version, required_components):
    global _waiting
    if application_name in _waiting:
        del _waiting[application_name]
    _waiting[application_name] = {
        'name': application_name, 'version': version, 'required_components': required_components, 'defer': None}
    return False


def _try_to_start_app(application_name, version, required_components):
    global _start
    global _waiting
    if not required_components:
        return _start_app(application_name, version)
    else:
        start_component = []
        for key in required_components.keys():
            if key in _start and required_components[key] == _start[key]:
                start_component.append(key)
        if len(start_component) == len(required_components):
            return _start_app(application_name, version)
        else:
            return _add_to_waiting_list(application_name, version, required_components)


class MestrSession(ApplicationSession):

    def onJoin(self, details):
        @inlineCallbacks
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
            global _start
            global _waiting
            import json
            ticket = json.loads(details['ticket']
                                )
            print("[MESTR] ", ticket)

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
                _waiting[application_name]['defer'] = ready_defered
                yield ready_defered

            print("[MESTR] ", _start)
            print("[MESTR] ", _waiting)
            for k in _start:
                if k in _waiting:
                    del _waiting[k]
            # backend role must be contains in the config.json
            # since we can't create them dynamically for the moment
            return "backend"

        return self.register(authenticate, 'mestr.authenticate')
        print("WAMP-Ticket dynamic authenticator registered!")
