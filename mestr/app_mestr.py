from autobahn_sync.core import AutobahnSync, DEFAULT_AUTOBAHN_ROUTER, DEFAULT_AUTOBAHN_REALM


class OnJoined:

    def __init__(self, application_name, version, required_components, app, callback=None):
        self.application_name = application_name
        self.version = version
        self.required_components = required_components
        self.app = app
        self.callback = callback

    def on_joined(self):
        self.app.session.call(
            'mestr.register', self.application_name, self.version, self.required_components)
        if self.callback:
            self.callback()


class AutobahnMestr:

    def __init__(self, application_name, version, required_components):
        self.app = None
        self._started = False
        self.application_name = application_name
        self.version = version
        self.required_components = required_components
        self._on_running_callbacks = []

    @property
    def session(self):
        return self.app.session

    def on_start_function(self):
        self._started = True
        for cb in self._on_running_callbacks:
            cb()
        self._on_running_callbacks = []

    def run_in_twisted(self, callback=None, url=DEFAULT_AUTOBAHN_ROUTER,
                       realm=DEFAULT_AUTOBAHN_REALM, blocking=False, **kwargs):
        self.app = AutobahnSync(self.application_name)
        app = self.app

        @app.subscribe('mestr.' + self.application_name + '.start')
        def start_app():
            self.on_start_function()
        joined = OnJoined(
            self.application_name, self.version, self.required_components, self.app, self.callback)
        self.app.run_in_twisted(joined, url, realm, blocking, **kwargs)

    def run(self, url=DEFAULT_AUTOBAHN_ROUTER, realm=DEFAULT_AUTOBAHN_REALM,
            blocking=False, **kwargs):
        self.app = AutobahnSync(self.application_name)
        app = self.app

        @app.subscribe('mestr.' + self.application_name + '.start')
        def start_app():
            self.on_start_function()
        joined = OnJoined(self.application_name, self.version, self.required_components, self.app)
        self.app.run(joined.on_joined, url, realm, blocking, **kwargs)

    def register(self, procedure=None, options=None):
        """Decorator for the :meth:`AutobahnButler.session.register`

        .. note::
            This decorator can be used before :meth:`AutobahnButler.run` is called.
            In such case the actual registration will be done at ``run()`` time.
        """

        def decorator(func):
            if self._started:
                self.app.session.register(endpoint=func, procedure=procedure, options=options)
            else:

                def registerer():
                    self.app.session.register(endpoint=func, procedure=procedure, options=options)

                # Wait for the WAMP session to be started
                self._on_running_callbacks.append(registerer)
            return func

        return decorator

    def subscribe(self, topic, options=None):
        """Decorator for the :meth:`AutobahnButler.session.subscribe`

        .. note::
            This decorator can be used before :meth:`AutobahnButler.run` is called.
            In such case the actual registration will be done at ``run()`` time.
        """

        def decorator(func):
            if self._started:
                self.app.session.subscribe(handler=func, topic=topic, options=options)
            else:

                def subscriber():
                    self.session.subscribe(handler=func, topic=topic, options=options)

                # Wait for the WAMP session to be started
                self._on_running_callbacks.append(subscriber)
            return func

        return decorator
