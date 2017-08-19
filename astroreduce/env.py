# BSD 3-Clause License
#
# Copyright (c) 2017, Zackary Parsons
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os

from typing import Callable, Dict, List, Tuple


_vars = {}
_var_hooks = {}
_VAR_DEFAULT_VAL = False


def _run_var_hooks(key: str, run_global_hooks: bool=False):
    """ Run all of the update hooks for the specified variable """
    if run_global_hooks:
        hook_key = ""
    else:
        hook_key = key

    hooks = _var_hooks.get(hook_key)
    if hooks is None:
        return

    for hook in hooks:
        hook(key, _vars.get(key))


def add_hook(key: str, hook: Callable):
    """ Add a hook to call when the variable is changed """
    hooks = _var_hooks.get(key)
    if hooks is None:
        hooks = []
        _var_hooks[key] = hooks
    hooks.append(hook)


def set(key: str, value: any, export: bool=False):
    """ Set the environmental variable given by "key=value" """
    _vars[key] = value
    if export:
        export_var(key)
    _run_var_hooks(key)
    _run_var_hooks(key, run_global_hooks=True)


def get(key: str) -> any:
    """ Get the environmental variable with the name "key" """
    value = _vars.get(key)
    if value is None:
        return _VAR_DEFAULT_VAL
    return value


def print_env():
    """ Print all environmental variables, values, and hooks """
    for key, value in _vars.items():
        print(key + "=" + value)
        hooks = _var_hooks.get(key)
        if hooks:
            for hook in hooks:
                print("`--> " + hook.__name__ + "()")


def import_sys_env():
    for key, value in os.environ.items():
        set(key, value)


def export_var(key: str):
    value = get(key)
    os.environ.set(key, value)
