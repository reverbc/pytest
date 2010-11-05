"""nose-compatibility plugin: allow to run nose test suites natively.

This is an experimental plugin for allowing to run tests written
in 'nosetests style with py.test.

Usage
-------------

type::

    py.test  # instead of 'nosetests'

and you should be able to run nose style tests and at the same
time can make full use of py.test's capabilities.

Supported nose Idioms
----------------------

* setup and teardown at module/class/method level
* SkipTest exceptions and markers
* setup/teardown decorators
* yield-based tests and their setup
* general usage of nose utilities

Unsupported idioms / issues
----------------------------------

- nose-style doctests are not collected and executed correctly,
  also fixtures don't work.

- no nose-configuration is recognized

If you find other issues or have suggestions please run::

    py.test --pastebin=all

and send the resulting URL to a py.test contact channel,
at best to the mailing list.
"""
import py
import inspect
import sys

def pytest_runtest_makereport(__multicall__, item, call):
    SkipTest = getattr(sys.modules.get('nose', None), 'SkipTest', None)
    if SkipTest:
        if call.excinfo and call.excinfo.errisinstance(SkipTest):
            # let's substitute the excinfo with a py.test.skip one
            call2 = call.__class__(lambda: py.test.skip(str(call.excinfo.value)), call.when)
            call.excinfo = call2.excinfo


def pytest_runtest_setup(item):
    if isinstance(item, (py.test.collect.Function)):
        if isinstance(item.parent, py.test.collect.Generator):
            gen = item.parent
            if not hasattr(gen, '_nosegensetup'):
                call_optional(gen.obj, 'setup')
                if isinstance(gen.parent, py.test.collect.Instance):
                    call_optional(gen.parent.obj, 'setup')
                gen._nosegensetup = True
        if not call_optional(item.obj, 'setup'):
            # call module level setup if there is no object level one
            call_optional(item.parent.obj, 'setup')

def pytest_runtest_teardown(item):
    if isinstance(item, py.test.collect.Function):
        if not call_optional(item.obj, 'teardown'):
            call_optional(item.parent.obj, 'teardown')
        #if hasattr(item.parent, '_nosegensetup'):
        #    #call_optional(item._nosegensetup, 'teardown')
        #    del item.parent._nosegensetup

def pytest_make_collect_report(collector):
    if isinstance(collector, py.test.collect.Generator):
        call_optional(collector.obj, 'setup')

def call_optional(obj, name):
    method = getattr(obj, name, None)
    if method:
        # If there's any problems allow the exception to raise rather than
        # silently ignoring them
        method()
        return True