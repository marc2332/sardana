#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""This module is part of the Python Sardana libray. It defines the base classes
for Sardana attributes"""

from __future__ import absolute_import

__all__ = ["SardanaAttribute", "SardanaSoftwareAttribute",
           "ScalarNumberAttribute", "SardanaAttributeConfiguration"]

__docformat__ = 'restructuredtext'

import weakref
import datetime

from taurus.external.ordereddict import OrderedDict

from .sardanaevent import EventGenerator, EventType
from .sardanadefs import ScalarNumberFilter
from .sardanavalue import SardanaValue
from .sardanaexception import SardanaException


class SardanaAttribute(EventGenerator):
    """Class representing an atomic attribute like position of a motor or a
    counter value"""

    def __init__(self, obj, name=None, initial_value=None, **kwargs):
        super(SardanaAttribute, self).__init__(**kwargs)
        if obj is not None:
            obj = weakref.ref(obj)
        self._obj = obj
        self.name = name or self.__class__.__name__
        self._r_value = None
        self._last_event_value = None
        self._w_value = None
        self.filter = lambda a, b: True
        self.config = SardanaAttributeConfiguration()
        if initial_value is not None:
            self.set_value(initial_value)

    def has_value(self):
        """Determines if the attribute's read value has been read at least once
        in the lifetime of the attribute.

        :return: True if the attribute has a read value stored or False otherwise
        :rtype: bool"""
        return self._has_value()

    def _has_value(self):
        return not self._r_value is None

    def has_write_value(self):
        """Determines if the attribute's write value has been read at least once
        in the lifetime of the attribute.

        :return: True if the attribute has a write value stored or False otherwise
        :rtype: bool"""
        return self._has_write_value()

    def _has_write_value(self):
        return self._w_value is not None

    def get_obj(self):
        """Returns the object which *owns* this attribute

        :return: the object which *owns* this attribute
        :rtype: obj"""
        return self._get_obj()

    def _get_obj(self):
        obj = self._obj
        if obj is not None:
            obj = obj()
        return obj

    def in_error(self):
        """Determines if this attribute is in error state.

        :return: True if the attribute is in error state or False otherwise
        :rtype: bool"""
        return self._in_error()

    def _in_error(self):
        return self.has_value() and self._r_value.error

    def set_value(self, value, exc_info=None, timestamp=None, propagate=1):
        """Sets the current read value and propagates the event (if
        propagate > 0).

        :param value: the new read value for this attribute. If a SardanaValue
                      is given, exc_info and timestamp are ignored (if given)
        :type value: obj or SardanaValue
        :param exc_info: exception information as returned by
                         :func:`sys.exc_info` [default: None, meaning no
                         exception]
        :type exc_info: tuple<3> or None
        :param timestamp: timestamp of attribute readout [default: None, meaning
                          create a 'now' timestamp]
        :type timestamp: float or None
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int"""
        return self._set_value(value, exc_info=exc_info, timestamp=timestamp,
                               propagate=propagate)

    def _set_value(self, value, exc_info=None, timestamp=None, propagate=1):
        if isinstance(value, SardanaValue):
            rvalue = value
        else:
            rvalue = SardanaValue(
                value=value, exc_info=exc_info, timestamp=timestamp)
        self._r_value = rvalue
        self.fire_read_event(propagate=propagate)

    def get_value(self):
        """Returns the last read value for this attribute.

        :return: the last read value for this attribute
        :rtype: obj

        :raises: :exc:`Exception` if no read value has been set yet"""
        return self._get_value()

    def _get_value(self):
        return self.get_value_obj().value

    def get_value_obj(self):
        """Returns the last read value for this attribute.

        :return: the last read value for this attribute
        :rtype: :class:`~sardana.sardanavalue.SardanaValue`

        :raises: :exc:`Exception` if no read value has been set yet"""
        return self._get_value_obj()

    def _get_value_obj(self):
        if not self.has_value():
            raise Exception("{0}.{1} doesn't have a read value yet".format(
                            self.obj.name, self.name))
        return self._r_value

    def set_write_value(self, w_value, timestamp=None, propagate=1):
        """Sets the current write value.

        :param value: the new write value for this attribute. If a SardanaValue
                      is given, timestamp is ignored (if given)
        :type value: obj or SardanaValue
        :param timestamp: timestamp of attribute write [default: None, meaning
                          create a 'now' timestamp]
        :type timestamp: float or None
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int"""
        return self._set_write_value(w_value, timestamp=timestamp,
                                     propagate=propagate)

    def _set_write_value(self, w_value, timestamp=None, propagate=1):
        if isinstance(w_value, SardanaValue):
            wvalue = w_value
        else:
            wvalue = SardanaValue(value=w_value, timestamp=timestamp)
        self._w_value = wvalue
        self.fire_write_event(propagate=propagate)

    def get_write_value(self):
        """Returns the last write value for this attribute.

        :return: the last write value for this attribute or None if value has
                 not been written yet
        :rtype: obj"""
        return self._get_write_value()

    def _get_write_value(self):
        w_value = self.get_write_value_obj()
        if w_value is not None:
            return w_value.value

    def get_write_value_obj(self):
        """Returns the last write value object for this attribute.

        :return: the last write value for this attribute or None if value has
                 not been written yet
        :rtype: :class:`~sardana.sardanavalue.SardanaValue`"""
        return self._get_write_value_obj()

    def _get_write_value_obj(self):
        if self.has_write_value():
            return self._w_value

    def get_exc_info(self):
        """Returns the exception information (like :func:`sys.exc_info`) about
        last attribute readout or None if last read did not generate an
        exception.

        :return: exception information or None
        :rtype: tuple<3> or None"""
        return self._get_exc_info()

    def _get_exc_info(self):
        exc_info = None
        if self.has_value():
            exc_info = self._r_value.exc_info
        return exc_info

    def accepts(self, propagate):
        if propagate < 1:
            return False
        if self._last_event_value is None:
            return True
        return propagate > 1 or self.filter(self.get_value(), self._last_event_value.value)

    def get_timestamp(self):
        """Returns the timestamp of the last readout or None if the attribute
        has never been read before

        :return: timestamp of the last readout or None
        :rtype: float or None"""
        return self._get_timestamp()

    def _get_timestamp(self):
        if self.has_value():
            return self._r_value.timestamp

    def get_write_timestamp(self):
        """Returns the timestamp of the last write or None if the attribute
        has never been written before

        :return: timestamp of the last write or None
        :rtype: float or None"""
        return self._get_write_timestamp()

    def _get_write_timestamp(self):
        if self.has_write_value():
            return self._w_value.timestamp

    def fire_write_event(self, propagate=1):
        """Fires an event to the listeners of the object which owns this
        attribute.

        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int"""
        if propagate < 1:
            return
        evt_type = EventType("w_" + self.name, priority=propagate)
        self.fire_event(evt_type, self)

    def fire_read_event(self, propagate=1):
        """Fires an event to the listeners of the object which owns this
        attribute.

        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int"""
        if self.accepts(propagate):
            obj = self.obj
            if obj is not None:
                self._last_event_value = self._r_value
                evt_type = EventType(self.name, priority=propagate)
                self.fire_event(evt_type, self)

    obj = property(get_obj, "container object for this attribute")
    value_obj = property(get_value_obj)
    write_value_obj = property(get_write_value_obj)
    value = property(get_value, set_value,
                     "current read value for this attribute")
    w_value = property(get_write_value, set_write_value,
                       "current write value for this attribute")
    timestamp = property(get_timestamp, doc="the read timestamp")
    w_timestamp = property(get_write_timestamp, doc="the write timestamp")
    error = property(in_error)
    exc_info = property(get_exc_info)

    def __repr__(self):
        v = None
        if self.in_error():
            v = "<Error>"
        elif self.has_value():
            v = self.value
        return "{0}(value={1})".format(self.name, v)

    def __str__(self):
        if self.has_value():
            value = "{0} at {1}".format(
                self.value, datetime.datetime.fromtimestamp(self.timestamp))
        else:
            value = "-----"
        if self.has_write_value():
            w_value = "{0} at {1}".format(
                self.w_value, datetime.datetime.fromtimestamp(self.w_timestamp))
        else:
            w_value = "-----"

        ret = """{0.__class__.__name__}(
       name = {0.name}
    manager = {0.obj}
       read = {1}
      write = {2})
""".format(self, value, w_value)
        return ret


class SardanaSoftwareAttribute(SardanaAttribute):
    """Class representing a software attribute. The difference between this and
    :class:`SardanaAttribute` is that, because it is a pure software attribute,
    there is no difference ever between the read and write values."""

    get_value = SardanaAttribute.get_value

    def set_value(self, value, exc_info=None, timestamp=None, propagate=1):
        """Sets the current read value and propagates the event (if
        propagate > 0).

        :param value: the new read value for this attribute
        :type value: obj
        :param exc_info: exception information as returned by
                         :func:`sys.exc_info` [default: None, meaning no
                         exception]
        :type exc_info: tuple<3> or None
        :param timestamp: timestamp of attribute readout [default: None, meaning
                          create a 'now' timestamp]
        :type timestamp: float or None
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int"""
        SardanaAttribute.set_value(self, value, exc_info=exc_info,
                                   timestamp=timestamp)
        self.set_write_value(value, timestamp=self.timestamp)

    value = property(get_value, set_value, "current value for this attribute")


class ScalarNumberAttribute(SardanaAttribute):
    """A :class:`SardanaAttribute` specialized for numbers"""

    def __init__(self, *args, **kwargs):
        SardanaAttribute.__init__(self, *args, **kwargs)
        self.filter = ScalarNumberFilter()

class Buffer(OrderedDict):
    """Buffer for objects which are identified by a unique idx and are ordered
    """

    def __init__(self, objs=None):
        OrderedDict.__init__(self)
        self._next_idx = 0
        self._last_chunk = None
        if objs is not None:
            self.extend(objs)

    def append(self, obj, idx=None, persistent=True):
        """Append a single object at the end of the buffer with a given index.

        :param obj: object to be appened to the buffer
        :type param: object
        :param idx: at which index append obj, None means assign at the end of
            the buffer
        :type idx: int
        :param persistent: whether object should be added to a persistent
            buffer or just as a last chunk
        :type param: bool
        """
        if idx is None:
            idx = self._next_idx
        self._last_chunk = OrderedDict()
        self._last_chunk[idx] = obj
        if persistent:
            self[idx] = obj
        self._next_idx = idx + 1

    def extend(self, objs, initial_idx=None, persistent=True):
        """Extend buffer with a list of objects assigning them consecutive
        indexes.

        :param objs: objects that extend the buffer
        :type param: list<object>
        :param initial_idx: at which index append the first object,
            the rest of them will be assigned the next consecutive indexes,
            None means assign at the end of the buffer
        :type idx: int
        :param persistent: whether object should be added to a persistent
            buffer or just as a last chunk
        :type param: bool
        """
        if initial_idx is None:
            initial_idx = self._next_idx
        self._last_chunk = OrderedDict()
        for idx, obj in enumerate(objs, initial_idx):
            self._last_chunk[idx] = obj
            if persistent:
                self[idx] = obj
        self._next_idx = idx + 1

    def get_last_chunk(self):
        return self._last_chunk

    def get_next_idx(self):
        return self._next_idx

    last_chunk = property(get_last_chunk,
        doc="chunk with last value(s) added to the buffer")
    next_idx = property(get_next_idx,
        doc="index that will be automatically assigned to the next value "\
            "added to the buffer (if not explicitly assigned by the user)")


class LateValueException(SardanaException):
    """Exception indicating that a given value is not present in the buffer and
    will not arrive yet (a newer value(s) were already added to the buffer).
    """
    pass


class EarlyValueException(SardanaException):
    """Exception indicating that a given value is not present in the buffer but
    there is still a chance that it will arrive (new newer values were added to
    the buffer yet.)
    """
    pass


class BufferedAttribute(SardanaAttribute):
    """A :class:`SardanaAttribute` specialized for buffering values.

    .. note::
        The BufferedAttribute class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    """

    def __init__(self, *args, **kwargs):
        self._buffered_attribute_listeners = []
        SardanaAttribute.__init__(self, *args, **kwargs)
        self._r_value_buffer = Buffer()

    def get_last_value_chunk(self):
        """Returns buffer of the read values added to the buffer as the last
        ones.

        :return: the last values add to this attribute
        :rtype: OrderedDict`"""

        return self._get_last_value_chunk()

    def _get_last_value_chunk(self):
        return self.value_buffer.last_chunk


    def get_value_buffer(self):
        """Returns buffer of the read values for this attribute.

        :return: the last read value for this attribute
        :rtype: :class:`~sardana.sardanavalue.SardanaValue`"""
        return self._get_value_buffer()

    def _get_value_buffer(self):
        return self._r_value_buffer

    def get_next_idx(self):
        return self._get_next_idx()

    def _get_next_idx(self):
        return self.value_buffer.next_idx

    def add_listener(self, listener):
        """Add listener

        :param listener: callable or object implementing event_received method
        """
        if not SardanaAttribute.add_listener(self, listener):
            return
        if isinstance(listener, BufferedAttribute) or\
            (hasattr(listener, "im_self") and
             isinstance(listener.im_self, BufferedAttribute)):
            self._buffered_attribute_listeners.append(listener)

    def remove_listener(self, listener):
        """Remove listener

        :param listener: callable or object implementing event_received method
        """
        if not SardanaAttribute.remove_listener(self, listener):
            return
        if isinstance(listener, BufferedAttribute) or\
            (hasattr(listener, "im_self") and
             isinstance(listener.im_self, BufferedAttribute)):
            self._buffered_attribute_listeners.remove(listener)

    def get_buffered_attribute_listeners(self):
        return self._buffered_attribute_listeners

    def has_buffered_attribute_listeners(self):
        return len(self.buffered_attribute_listeners) > 0

    def is_value_required(self, idx):
        """Check whether any of buffered attribute listeners still requires
        this value.

        :param idx: value's index
        :type idx: int
        """
        for element in self.obj.get_pseudo_elements():
            value_attr = element.get_value_attribute()
            if value_attr.next_idx <= idx:
                return True
        return False

    def get_value(self, idx=None):
        """Get value

        :param idx: value's index
        :type idx: int
        """
        if idx is None:
            value = SardanaAttribute.get_value(self)
        else:
            try:
                value_obj = self._r_value_buffer[idx]
                value = value_obj.value
            except KeyError:
                msg = "value with %s index is not in buffer"
                if self.next_idx > idx:
                    raise LateValueException(msg)
                else:
                    raise EarlyValueException(msg)
        return value

    def remove_value(self, idx):
        """Remove value

        :param idx: value's index
        :type idx: int
        """
        try:
            self._r_value_buffer.pop(idx)
        except KeyError:
            pass

    def append_value_buffer(self, value, idx=None, propagate=1):
        """Append value to the value buffer and propagate the event
        (if porpagate > 0). The new value will be assigned index passed as idx
        or the next index in the buffer.

        :param values: the new read values for this attribute
        :type values: seq<SardanaValue>
        :param idx: the starting index
        :type idx: int
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int
        """

        self._append_value_buffer(value, idx, propagate)

    def _append_value_buffer(self, value, idx=None, propagate=1):
        persistent = self.obj.has_pseudo_elements()
        self._r_value_buffer.append(value, idx, persistent)
        self.fire_read_buffer_event(propagate)

    def extend_value_buffer(self, values, idx=None, propagate=1):
        """Extend value buffer with values and propagate the event
        (if porpagate > 0). The new values will be assigned consecutive indexes
        starting from idx or in continuation to the last value in the buffer if
        idx is None.

        :param values: the new read values for this attribute
        :type values: seq<SardanaValue>
        :param idx: the starting index
        :type idx: int
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int
        """
        self._extend_value_buffer(values, idx, propagate)

    def _extend_value_buffer(self, values, idx=None, propagate=1):
        if len(values) == 0:
            return
        persistent = self.obj.has_pseudo_elements()
        self._r_value_buffer.extend(values, idx, persistent)
        self.fire_read_buffer_event(propagate)

    def fire_read_buffer_event(self, propagate=1):
        """Fires an event to the listeners of the object which owns this
        attribute.

        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int

        .. todo:: implement filtering depending on propagate value
        """
        obj = self.obj
        if obj is not None:
            evt_type = EventType(self.name + "_buffer", priority=propagate)
            self.fire_event(evt_type, self)

    def clear_value_buffer(self):
        """Clear value buffer."""
        self._clear_value_buffer()

    def _clear_value_buffer(self):
        self._r_value_buffer = Buffer()

    last_value_chunk = property(get_last_value_chunk,
        doc="chunk with the last added read values")
    value_buffer = property(get_value_buffer, "buffer with read values")
    buffered_attribute_listeners = property(get_buffered_attribute_listeners,
        doc="list of listeners of BufferedAttribute type")
    next_idx = property(get_next_idx,
        doc="index that will be automatically assigned to the next value "\
            " appended to the buffer if not explicitly assigned")

class SardanaAttributeConfiguration(object):
    """Storage class for :class:`SardanaAttribute` information (like ranges)"""
    NoRange = float('-inf'), float('inf')

    def __init__(self):
        self.range = self.NoRange
        self.alarm = self.NoRange
        self.warning = self.NoRange
