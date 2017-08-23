#
# FIXME: This isn't a very well written test case.
# I think it could be more flushed out.
#

import unittest

import os

from .. import env

_hook_test_before_var = False
_hook_test_after_var = False

def _hook_test_before_func(key, value):
    global _hook_test_before_var
    _hook_test_before_var = value

def _hook_test_after_func(key, value):
    global _hook_test_after_var
    _hook_test_after_var = value

class TestEnv(unittest.TestCase):
    def setUp(self):
        env._vars = {}
        env._var_hooks = {}

    def test_set_get(self):
        env.set("TestString", "Hello")
        env.set("TestInt", 5)

        string_var = env.get("TestString")
        int_var = env.get("TestInt")

        self.assertEqual(string_var, "Hello")
        self.assertEqual(int_var, 5)

    def test_get_default(self):
        ret = env.get("NwTeAaOk")

        self.assertIs(ret, False)

    def test_import_sys_env(self):
        os.environ["TestString"] = "World"
        env.import_sys_env()
        string_var = env.get("TestString")

        self.assertEqual(string_var, "World")

    def test_export_var(self):
        # Clear the variable if it exists already
        if os.environ.get("TestExportVar"):
            os.environ.pop("TestExportVar")

        env.set("TestExportVar", "Foo")
        no_ret = os.environ.get("TestExportVar") # Should be None since we haven't exported yet
        env.export_var("TestExportVar")
        ret = os.environ.get("TestExportVar")

        self.assertIs(no_ret, None)
        self.assertEqual(ret, "Foo")

    def test_add_hook(self):
        global _hook_test_before_var
        global _hook_test_after_var
        _hook_test_before_var = False
        _hook_test_after_var = False

        env.add_hook("HookBefore", _hook_test_before_func) # Add hook before var is defined
        env.set("HookBefore", "BeforeVarInit")
        env.set("HookAfter", "AfterVarInit")
        env.add_hook("HookAfter", _hook_test_after_func) # Add hook after var is defined

        self.assertIs(_hook_test_before_var, "BeforeVarInit")
        self.assertIs(_hook_test_after_var, False)

        env.set("HookBefore", "BeforeVarChanged")
        env.set("HookAfter", "AfterVarChanged")

        self.assertEqual(_hook_test_before_var, "BeforeVarChanged")
        self.assertEqual(_hook_test_after_var, "AfterVarChanged")


if __name__ == "__main__":
    unittest.main()
