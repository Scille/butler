from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks, returnValue
from autobahn.wamp.exception import ApplicationError
from autobahn.twisted.wamp import ApplicationSession

_start = {}
_waiting = {}


def _start_app(application_name, version):
    global _start
    global _waiting
    if application_name in _start and _start[application_name] == version:
        return True
    _start[application_name] = version

    for key in _waiting:
        if key not in _start:
            _waiting[key]['defer'].callback("result")
    return True


def _add_to_waiting_list(application_name, version, required_components):
    global _waiting
    if application_name not in _waiting:
        _waiting[application_name] = {'name': application_name,
                                      'version': version,
                                      'required_components': required_components,
                                      'defer': None,
                                      'call': False}
    return False


def defer_try_start_app(result, application_name, version, required_components):
    return _try_to_start_app(application_name, version, required_components)


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


def remove_element(dico, key):
    new_dict = dico.copy()
    del new_dict[key]
    return new_dict


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
    if 'application_name' not in ticket and 'version' not in ticket:
        raise ApplicationError(
            'could not start the authentication of an app,\
             field application_name or version is missing')
    application_name = ticket['application_name']
    version = ticket['version']

    required_components = ticket[
        'required_components'] if 'required_components' in ticket else {}
    if not _try_to_start_app(application_name, version, required_components):
        ready_defered = defer.Deferred()
        ready_defered.addCallback(defer_try_start_app,
                                  application_name=application_name,
                                  version=version,
                                  required_components=required_components)
        _waiting[application_name]['defer'] = ready_defered
        yield ready_defered

    print("[MESTR] start app: ", _start)
    print("[MESTR] waiting app: ", _waiting)

    for k in _start:
        if k in _waiting:
            _waiting = remove_element(_waiting, k)
    # backend role must be contains in the config.json
    # since we can't create them dynamically for the moment
    returnValue("backend")


class MestrSession(ApplicationSession):  # pragma: no cover

    def onJoin(self, details):  # pragma: no cover
        return self.register(authenticate, 'mestr.authenticate')
