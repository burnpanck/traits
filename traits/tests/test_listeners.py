#  Test the 'add_trait_listener', 'remove_trait_listener' interface to
#  the HasTraits class.
#
#  Written by: David C. Morrill
#
#  Date: 09/07/2005
#
#  (c) Copyright 2005 by Enthought, Inc.
#
#  Copyright (c) 2007, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  License included in /LICENSE.txt and may be redistributed only under the
#  conditions described in the aforementioned license.  The license is also
#  available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!

from __future__ import absolute_import

import contextlib
import cStringIO
import sys
import threading
import time

from traits.testing.unittest_tools import unittest

from ..api import HasTraits, Str, Int, Float, Any, Event, Instance
from ..api import push_exception_handler, pop_exception_handler


@contextlib.contextmanager
def captured_stderr():
    """
    Return a context manager that directs all stderr output to a string.

    """
    new_stderr = cStringIO.StringIO()
    original_stderr = sys.stderr
    sys.stderr = new_stderr
    try:
        yield new_stderr
    finally:
        sys.stderr = original_stderr


class GenerateEvents(HasTraits):
    name = Str
    age = Int
    weight = Float

events = {}  # dict of events


class ListenEvents(HasTraits):

    #  'GenerateEvents' event interface:
    #  the events are stored in the dict 'events'

    def _name_changed(self, object, name, old, new):
        events["_name_changed"] = (name, old, new)

    def _age_changed(self, object, name, old, new):
        events["_age_changed"] = (name, old, new)

    def _weight_changed(self, object, name, old, new):
        events["_weight_changed"] = (name, old, new)

    def alt_name_changed(self, object, name, old, new):
        events["alt_name_changed"] = (name, old, new)

    def alt_weight_changed(self, object, name, old, new):
        events["alt_weight_changed"] = (name, old, new)


class Test_Listeners(unittest.TestCase):

    def test(self):
        global events

        # FIXME: comparing floats
        ge = GenerateEvents()
        le = ListenEvents()

        # Starting test: No Listeners
        ge.set(name='Joe', age=22, weight=152.0)

        # Adding default listener
        ge.add_trait_listener(le)
        events = {}
        ge.set(name='Mike', age=34, weight=178.0)
        self.assertEqual(events, {
            '_age_changed': ('age', 22, 34),
            '_weight_changed': ('weight', 152.0, 178.0),
            '_name_changed': ('name', 'Joe', 'Mike'),
            })

        # Adding alternate listener
        ge.add_trait_listener(le, 'alt')
        events = {}
        ge.set(name='Gertrude', age=39, weight=108.0)
        self.assertEqual(events, {
            '_age_changed': ('age', 34, 39),
            '_name_changed': ('name', 'Mike', 'Gertrude'),
            '_weight_changed': ('weight', 178.0, 108.0),
            'alt_name_changed': ('name', 'Mike', 'Gertrude'),
            'alt_weight_changed': ('weight', 178.0, 108.0),
            })

        # Removing default listener
        ge.remove_trait_listener(le)
        events = {}
        ge.set(name='Sally', age=46, weight=118.0)
        self.assertEqual(events, {
            'alt_name_changed': ('name', 'Gertrude', 'Sally'),
            'alt_weight_changed': ('weight', 108.0, 118.0),
            })

        # Removing alternate listener
        ge.remove_trait_listener(le, 'alt')
        events = {}
        ge.set(name='Ralph', age=29, weight=198.0)
        self.assertEqual(events, {})


class A(HasTraits):
    exception = Any

    foo = Event

    def foo_changed_handler(self):
        pass


def foo_writer(a, stop_event):
    while not stop_event.is_set():
        try:
            a.foo = True
        except Exception as e:
            a.exception = e


class TestRaceCondition(unittest.TestCase):
    def setUp(self):
        push_exception_handler(
            handler=lambda *args: None,
            reraise_exceptions=True,
            main=True,
            )

    def tearDown(self):
        pop_exception_handler()

    def test_listener_thread_safety(self):
        # Regression test for GitHub issue #56
        a = A()
        stop_event = threading.Event()

        t = threading.Thread(target=foo_writer, args=(a, stop_event))
        t.start()

        for _ in xrange(100):
            a.on_trait_change(a.foo_changed_handler, 'foo')
            time.sleep(0.0001)  # encourage thread-switch
            a.on_trait_change(a.foo_changed_handler, 'foo', remove=True)

        stop_event.set()
        t.join()

        self.assertTrue(a.exception is None)

    def test_listener_deleted_race(self):
        # Regression test for exception that occurred when the listener_deleted
        # method is called after the dispose method on a
        # TraitsChangeNotifyWrapper.
        class SlowListener(HasTraits):
            def handle_age_change(self):
                time.sleep(1.0)

        def worker_thread(event_source, start_event):
            # Wait until the listener is set up on the main thread, then fire
            # the event.
            start_event.wait()
            event_source.age = 11

        def main_thread(event_source, start_event):
            listener = SlowListener()
            event_source.on_trait_change(listener.handle_age_change, 'age')
            start_event.set()
            # Allow time to make sure that we're in the middle of handling an
            # event.
            time.sleep(0.5)
            event_source.on_trait_change(
                listener.handle_age_change, 'age', remove=True)

        # Previously, a ValueError would be raised on the worker thread
        # during (normal refcount-based) garbage collection.  That
        # ValueError is ignored by the Python system, so the only
        # visible effect is the output to stderr.
        with captured_stderr() as s:
            start_event = threading.Event()
            event_source = GenerateEvents(age=10)
            t = threading.Thread(
                target=worker_thread,
                args=(event_source, start_event),
                )
            t.start()
            main_thread(event_source, start_event)
            t.join()

        self.assertNotIn('Exception', s.getvalue())

class UnhashableHasTraits(HasTraits):
    a = Any
    def __eq__(self,other):
        return type(self) == type(other)
    # On python 3, __hash__ is implicitely set to None when a class
    # defines __eq__ but not hash (see: https://docs.python.org/3/reference/datamodel.html#object.__hash__)
    # On python 2, we need to do this manually to make this class unhashable.
    __hash__ = None
        

class Container(HasTraits):
    sub = Instance(UnhashableHasTraits)

class TestUnhashableHasTraits(unittest.TestCase):
    def setUp(self):
        push_exception_handler(
            handler=lambda *args: None,
            reraise_exceptions=True,
            main=True,
            )

    def tearDown(self):
        pop_exception_handler()

    def test_unhashable_is_unhashable(self):
        obj = UnhashableHasTraits()
        with self.assertRaises(TypeError):
            hash(obj)
        
    def test_can_listen_to_unhashable(self):
        obj = UnhashableHasTraits()
        events = []
        def obj_a_changed(new):
            events.append(new)
        obj.on_trait_change(obj_a_changed,'a')
        obj.a = 3
        self.assertSequenceEqual(events,[3])
    
    def test_unshashable_intermediate(self):
        obj = Container(sub = UnhashableHasTraits(a=1))
        events = []
        def obj_sub_a_changed(new):
            events.append(new)
        def obj_sub_a2_changed(new):
            events.append(new)
        obj.on_trait_change(obj_sub_a_changed,'sub.a')
        obj.sub.a = 2
        # this one would raise an exception in traits 4.5.0, as the listener
        # machinery would try to put 'obj' into a dict.
        obj.sub = UnhashableHasTraits(a=3)
        obj.sub.a = 4
        self.assertSequenceEqual(events,[2,3,4])

# Run the unit tests (if invoked from the command line):
if __name__ == '__main__':
    unittest.main()
