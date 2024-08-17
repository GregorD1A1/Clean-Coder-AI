# -*- coding: utf-8 -*-

"""
pyee supplies a `EventEmitter` class that is similar to the
`EventEmitter` class from Node.js. In addition, it supplies the subclasses
`AsyncIOEventEmitter`, `TwistedEventEmitter` and `ExecutorEventEmitter`
for supporting async and threaded execution with asyncio, twisted, and
concurrent.futures Executors respectively, as supported by the environment.

# Example

```text
In [1]: from pyee.base import EventEmitter

In [2]: ee = EventEmitter()

In [3]: @ee.on('event')
   ...: def event_handler():
   ...:     print('BANG BANG')
   ...:

In [4]: ee.emit('event')
BANG BANG

In [5]:
```

"""

from warnings import warn

from pyee.base import EventEmitter as EventEmitter
from pyee.base import PyeeException


class BaseEventEmitter(EventEmitter):
    """
    BaseEventEmitter is deprecated and an alias for EventEmitter.
    """

    def __init__(self):
        warn(
            DeprecationWarning(
                "pyee.BaseEventEmitter is deprecated and will be removed in a "
                "future major version; you should instead use pyee.EventEmitter."
            )
        )

        super(BaseEventEmitter, self).__init__()


__all__ = ["BaseEventEmitter", "EventEmitter", "PyeeException"]

try:
    from pyee.asyncio import AsyncIOEventEmitter as _AsyncIOEventEmitter  # noqa

    class AsyncIOEventEmitter(_AsyncIOEventEmitter):
        """
        AsyncIOEventEmitter has been moved to the pyee.asyncio module.
        """

        def __init__(self, loop=None):
            warn(
                DeprecationWarning(
                    "pyee.AsyncIOEventEmitter has been moved to the pyee.asyncio "
                    "module."
                )
            )
            super(AsyncIOEventEmitter, self).__init__(loop=loop)

    __all__.append("AsyncIOEventEmitter")
except ImportError:
    pass

try:
    from pyee.twisted import TwistedEventEmitter as _TwistedEventEmitter  # noqa

    class TwistedEventEmitter(_TwistedEventEmitter):
        """
        TwistedEventEmitter has been moved to the pyee.twisted module.
        """

        def __init__(self):
            warn(
                DeprecationWarning(
                    "pyee.TwistedEventEmitter has been moved to the pyee.twisted "
                    "module."
                )
            )
            super(TwistedEventEmitter, self).__init__()

    __all__.append("TwistedEventEmitter")
except ImportError:
    pass

try:
    from pyee.executor import ExecutorEventEmitter as _ExecutorEventEmitter  # noqa

    class ExecutorEventEmitter(_ExecutorEventEmitter):
        """
        ExecutorEventEmitter has been moved to the pyee.executor module.
        """

        def __init__(self, executor=None):
            warn(
                DeprecationWarning(
                    "pyee.ExecutorEventEmitter has been moved to the pyee.executor "
                    "module."
                )
            )
            super(ExecutorEventEmitter, self).__init__(executor=executor)

    __all__.append("ExecutorEventEmitter")
except ImportError:
    pass

try:
    from pyee.trio import TrioEventEmitter as _TrioEventEmitter  # noqa

    class TrioEventEmitter(_TrioEventEmitter):
        """
        TrioEventEmitter has been moved to the pyee.trio module.
        """

        def __init__(self, nursery=None, manager=None):
            warn(
                DeprecationWarning(
                    "pyee.TrioEventEmitter has been moved to the pyee.trio module."
                )
            )

            super(TrioEventEmitter, self).__init__(nursery=nursery, manager=manager)

    __all__.append("TrioEventEmitter")
except (ImportError, SyntaxError):
    pass
