#!/usr/bin/env python -t
# -*- coding: utf-8 -*-

# Copyright (C) 2014  Jonathan Delvaux <pyshell@djoproject.net>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# TODO
#   prevoir un system simple pour permettre au loader d'indiquer si
#   des elements doivent etre sauver et un system pour les sauver

#   pour l'instant: procedure, environment, contexte, variable

#   each item can hold three hash:
#       hash_file: computed at file loading (set to None if item is
#                                            not updated)
#       hash_default (static): computed at registering, always the same from
#       an execution to another
#       current_hash: not computed but could be computed at any time

#   if hash_file is None and current_hash == hash_default => not a candidate to
#                                                            be saved
#   if hash_file is not None
#       if current_hash == hash_file => candidate to be save + does not
#                                       trigger file regeneration
#       if current_hash == hash_default => need to be remove of the file +
#                                          trigger file regeneration
#       else => need to be saved + trigger file regeneration

import heapq
import inspect
import traceback

from pyshell.loader.exception import LoadException
from pyshell.loader.exception import RegisterException
from pyshell.utils.constants import DEFAULT_PROFILE_NAME
from pyshell.utils.constants import STATE_LOADED
from pyshell.utils.constants import STATE_LOADED_E
from pyshell.utils.constants import STATE_UNLOADED
from pyshell.utils.constants import STATE_UNLOADED_E
from pyshell.utils.exception import ListOfException


def getAndInitCallerModule(caller_loader_key,
                           caller_loader_class_definition,
                           profile=None,
                           module_level=3):
    frm = inspect.stack()[module_level]
    mod = inspect.getmodule(frm[0])

    if hasattr(mod, "_loaders"):
        # must be an instance of GlobalLoader
        if not isinstance(mod._loaders, GlobalLoader):
            excmsg = ("(loader) getAndInitCallerModule, the stored loader in"
                      " the module '"+str(mod)+"' is not an instance of "
                      "GlobalLoader, get '"+str(type(mod._loaders))+"'")
            raise RegisterException(excmsg)
    else:
        setattr(mod, "_loaders", GlobalLoader())  # init loaders dictionnary

    return mod._loaders.getOrCreateLoader(caller_loader_key,
                                          caller_loader_class_definition,
                                          profile)


class AbstractLoader(object):
    def __init__(self, priority=100):
        self.last_exception = None
        self.priority = priority

    def load(self, parameter_manager, profile=None):
        pass  # TO OVERRIDE

    def unload(self, parameter_manager, profile=None):
        pass  # TO OVERRIDE

    def reload(self, parameter_manager, profile=None):
        self.unload(parameter_manager, profile)
        self.load(parameter_manager, profile)
        # CAN BE OVERRIDEN TOO

    def getPriority(self):
        return self.priority
        # CAN BE OVERRIDEN TOO


class GlobalLoader(AbstractLoader):
    def __init__(self):
        AbstractLoader.__init__(self)
        self.profile_list = {}
        self.last_updated_profile = None

    def getOrCreateLoader(self, loader_name, class_definition, profile=None):
        if profile is None:
            profile = DEFAULT_PROFILE_NAME

        if (profile in self.profile_list and
           loader_name in self.profile_list[profile]):
            return self.profile_list[profile][loader_name]

        # the loader does not exist, need to create it
        try:
            # need a child class of AbstractLoader
            if (not issubclass(class_definition, AbstractLoader) or
               class_definition.__name__ == "AbstractLoader"):
                excmsg = ("(GlobalLoader) getOrCreateLoader, try to create a "
                          "loader with an unallowed class '" +
                          str(class_definition)+"', must be a class definition"
                          " inheriting from AbstractLoader")
                raise RegisterException(excmsg)

        # raise by issubclass if one of the two argument
        # is not a class definition
        except TypeError:
            excmsg = ("(GlobalLoader) getOrCreateLoader, expected a class "
                      "definition, got '"+str(class_definition)+"', must be a"
                      " class definition inheriting from AbstractLoader")
            raise RegisterException(excmsg)

        if profile not in self.profile_list:
            self.profile_list[profile] = {}

        loader = class_definition()
        self.profile_list[profile][loader_name] = loader

        return loader

    def _innerLoad(self,
                   method_name,
                   parameter_manager,
                   profile,
                   next_state,
                   next_state_if_error):
        exceptions = ListOfException()

        # no loader available for this profile
        if profile not in self.profile_list:
            return

        loaders = self.profile_list[profile]

        loaders_heap = []

        insert_order = 0
        for loader in loaders.values():
            heapq.heappush(loaders_heap, (loader.getPriority(),
                                          insert_order,
                                          loader,))
            insert_order += 1

        while len(loaders_heap) > 0:
            priority, insert_order, loader = heapq.heappop(loaders_heap)
            # no need to test if attribute exist, it is supposed to call
            # load/unload or reload and loader is suppose to be an
            # AbstractLoader
            meth_to_call = getattr(loader, method_name)

            try:
                meth_to_call(parameter_manager, profile)
                loader.last_exception = None
            except Exception as ex:
                # TODO is it used somewhere ? will be overwrite on reload if
                # error on unload and on load
                loader.last_exception = ex
                exceptions.addException(ex)
                loader.last_exception.stackTrace = traceback.format_exc()

        if exceptions.isThrowable():
            self.last_updated_profile = (profile, next_state_if_error,)
            raise exceptions

        self.last_updated_profile = (profile, next_state,)

    _loadAllowedState = (STATE_UNLOADED, STATE_UNLOADED_E,)
    _unloadAllowedState = (STATE_LOADED, STATE_LOADED_E,)

    def load(self, parameter_manager, profile=None):
        if profile is None:
            profile = DEFAULT_PROFILE_NAME

        if (self.last_updated_profile is not None and
           self.last_updated_profile[1] not in GlobalLoader._loadAllowedState):
            if profile == self.last_updated_profile[0]:
                # TODO should we raise an exception if already loaded ?
                # excmsg = ("(GlobalLoader) 'load', profile '"+str(profile) +
                #           "' is already loaded")
                # raise LoadException(excmsg)
                return
            else:
                excmsg = ("(GlobalLoader) 'load', profile '"+str(profile)+"' "
                          "is not loaded but an other profile '" +
                          str(self.last_updated_profile[0])+"' is already "
                          "loaded")
                raise LoadException(excmsg)

        self._innerLoad("load",
                        parameter_manager=parameter_manager,
                        profile=profile,
                        next_state=STATE_LOADED,
                        next_state_if_error=STATE_LOADED_E)

    def unload(self, parameter_manager, profile=None):
        if profile is None:
            profile = DEFAULT_PROFILE_NAME

        allowed_state = GlobalLoader._unloadAllowedState
        if (self.last_updated_profile is None or
           self.last_updated_profile[0] != profile or
           self.last_updated_profile[1] not in allowed_state):
            excmsg = ("(GlobalLoader) 'unload', profile '"+str(profile)+"' is"
                      " not loaded")
            raise LoadException(excmsg)

        self._innerLoad("unload",
                        parameter_manager=parameter_manager,
                        profile=profile,
                        next_state=STATE_UNLOADED,
                        next_state_if_error=STATE_UNLOADED_E)

    def reload(self, parameter_manager, profile=None):
        if profile is None:
            profile = DEFAULT_PROFILE_NAME

        allowed_state = GlobalLoader._unloadAllowedState
        if (self.last_updated_profile is None or
           self.last_updated_profile[0] != profile or
           self.last_updated_profile[1] not in allowed_state):
            excmsg = ("(GlobalLoader) 'reload', profile '"+str(profile)+"' is"
                      " not loaded")
            raise LoadException(excmsg)

        self._innerLoad("reload",
                        parameter_manager=parameter_manager,
                        profile=profile,
                        next_state=STATE_LOADED,
                        next_state_if_error=STATE_LOADED_E)
