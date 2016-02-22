#!/usr/bin/env python -t
# -*- coding: utf-8 -*-

# Copyright (C) 2015  Jonathan Delvaux <pyshell@djoproject.net>

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

from pyshell.arg.argchecker import DefaultInstanceArgChecker
from pyshell.system.environment import EnvironmentParameter
from pyshell.system.parameter import ParameterManager


class CryptographicKeyParameterManager(ParameterManager):
    def getAllowedType(self):
        return CryptographicKeyParameter


class CryptographicKeyParameter(EnvironmentParameter):
    def __init__(self, value, settings=None):
        default_arg_checker = DefaultInstanceArgChecker.getKeyChecker()
        EnvironmentParameter.__init__(self,
                                      value,
                                      default_arg_checker,
                                      settings=settings)
