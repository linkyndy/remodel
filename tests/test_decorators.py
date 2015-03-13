from remodel.decorators import callback

from . import BaseTestCase


class CallbackTests(BaseTestCase):
    def test_decorated_function_attribute(self):
        @callback('attribute')
        def func():
            pass

        assert hasattr(func, 'attribute')
        assert func.attribute is True
