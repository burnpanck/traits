""" Helper module, providing a common API for tasks that require a different implementation in python 2 and 3.
"""

from __future__ import division, absolute_import

import sys


if sys.version_info[0] < 3:
    import string
    str_find = string.find
    str_rfind = string.rfind
else:
    str_find = str.find
    str_rfind = str.rfind

if sys.version_info[0] < 3:
    from types import InstanceType,ClassType
    def is_old_style_instance(obj):
        return type(obj) is InstanceType
    def is_old_style_class(obj):
        return type(obj) is ClassType
    def is_InstanceType(obj):
        return obj is InstanceType
    def is_ClassType(obj):
        return obj is ClassType
else:
    def is_old_style_instance(obj):
        return False
    def is_old_style_instance(obj):
        return False
    def is_InstanceType(obj):
        return False
    def is_ClassType(obj):
        return False


if sys.version_info[0] < 3:
    from types import InstanceType
    def type_w_old_style(obj):
        the_type = type(obj)
        if the_type is InstanceType:
            # Old-style class.
            the_type = obj.__class__
        return the_type
else:
    type_w_old_style = type

if sys.version_info[0] < 3:
    from types import ClassType
    ClassTypes    = ( ClassType, type )
else:
    ClassTypes    = ( type, )


import contextlib
if sys.version_info[0] < 3:
    def nested_context_mgrs(*args):
        return contextlib.nested(*args)
else:
    class nested_context_mgrs(contextlib.ExitStack):
        """ Emulation of python 2's :py:class:`contextlib.nested`.
        
        It has gone from python 3 due to it's deprecation status
        in python 2.
        
        Note that :py:class:`contextlib.nested` was deprecated for
        a reason: It has issues with context managers that fail
        during init. The same caveats also apply here.
        So do not use this unless really necessary!
        """
        def __init__(self,*args):
            super(nested_context_mgrs,self).__init__()
            self._ctxt_mgrs = args
        
        def __enter__(self):
            ret = []
            try:
                for mgr in self._ctxt_mgrs:
                    ret.append(self.enter_context(mgr))
            except:
                self.close()
                raise
            return tuple(ret)

if sys.version_info[0] < 3:
    def assertCountEqual(self,itemsA,itemsB):
        self.assertItemsEqual(itemsA,itemsB)
else:
    def assertCountEqual(self,itemsA,itemsB):
        self.assertCountEqual(itemsA,itemsB)
    