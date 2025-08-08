"""
Unit tests for configomatic.utils module.
"""

import unittest

from configomatic.utils import merge, snake_to_pascal


class TestSnakeToPascal(unittest.TestCase):
    """Test cases for snake_to_pascal function."""

    def test_simple_snake_case(self):
        """Test conversion of simple snake_case strings."""
        self.assertEqual(snake_to_pascal("hello_world"), "helloWorld")

    def test_single_word(self):
        """Test conversion of a single word (no underscores)."""
        self.assertEqual(snake_to_pascal("hello"), "hello")

    def test_multiple_underscores(self):
        """Test conversion with multiple underscores."""
        self.assertEqual(snake_to_pascal("this_is_a_test"), "thisIsATest")

    def test_empty_string(self):
        """Test conversion of an empty string."""
        self.assertEqual(snake_to_pascal(""), "")

    def test_single_underscore(self):
        """Test conversion with just an underscore."""
        self.assertEqual(snake_to_pascal("_"), "")

    def test_leading_underscore(self):
        """Test conversion with leading underscore."""
        self.assertEqual(snake_to_pascal("_hello_world"), "HelloWorld")

    def test_trailing_underscore(self):
        """Test conversion with trailing underscore."""
        self.assertEqual(snake_to_pascal("hello_world_"), "helloWorld")

    def test_consecutive_underscores(self):
        """Test conversion with consecutive underscores."""
        self.assertEqual(snake_to_pascal("hello__world"), "helloWorld")

    def test_numbers_in_snake_case(self):
        """Test conversion with numbers in the string."""
        self.assertEqual(snake_to_pascal("test_123_case"), "test123Case")

    def test_mixed_case_input(self):
        """Test conversion with mixed case input."""
        self.assertEqual(snake_to_pascal("Hello_World"), "helloWorld")

    def test_all_caps_segments(self):
        """Test conversion with all caps segments."""
        self.assertEqual(snake_to_pascal("HTTP_STATUS_CODE"), "httpStatusCode")


class TestMerge(unittest.TestCase):
    """Test cases for merge function."""

    def test_merge_empty_dicts(self):
        """Test merging empty dictionaries."""
        result = merge({}, {})
        self.assertEqual(result, {})

    def test_merge_with_empty_defaults(self):
        """Test merging with empty defaults."""
        defaults = {}
        override = {"a": 1, "b": 2}
        result = merge(defaults, override)
        self.assertEqual(result, {"a": 1, "b": 2})

    def test_merge_with_empty_override(self):
        """Test merging with empty override."""
        defaults = {"a": 1, "b": 2}
        override = {}
        result = merge(defaults, override)
        self.assertEqual(result, {"a": 1, "b": 2})

    def test_simple_merge(self):
        """Test simple merge without conflicts."""
        defaults = {"a": 1, "b": 2}
        override = {"c": 3, "d": 4}
        result = merge(defaults, override)
        self.assertEqual(result, {"a": 1, "b": 2, "c": 3, "d": 4})

    def test_merge_with_override(self):
        """Test merge with key conflicts - override should win."""
        defaults = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = merge(defaults, override)
        self.assertEqual(result, {"a": 1, "b": 3, "c": 4})

    def test_deep_merge(self):
        """Test deep merging of nested dictionaries."""
        defaults = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 4, "z": 5}, "c": 6}
        result = merge(defaults, override)
        expected = {"a": {"x": 1, "y": 4, "z": 5}, "b": 3, "c": 6}
        self.assertEqual(result, expected)

    def test_multiple_overrides(self):
        """Test merging with multiple override dictionaries."""
        defaults = {"a": 1}
        override1 = {"b": 2}
        override2 = {"c": 3}
        override3 = {"a": 4}
        result = merge(defaults, override1, override2, override3)
        self.assertEqual(result, {"a": 4, "b": 2, "c": 3})

    def test_multiple_overrides_precedence(self):
        """Test that later overrides have higher precedence."""
        defaults = {"a": 1, "b": 1}
        override1 = {"a": 2, "b": 2}
        override2 = {"a": 3}
        result = merge(defaults, override1, override2)
        self.assertEqual(result, {"a": 3, "b": 2})

    def test_deep_merge_multiple_levels(self):
        """Test deep merging with multiple nesting levels."""
        defaults = {"level1": {"level2": {"level3": {"a": 1, "b": 2}}}}
        override = {"level1": {"level2": {"level3": {"b": 3, "c": 4}}}}
        result = merge(defaults, override)
        expected = {"level1": {"level2": {"level3": {"a": 1, "b": 3, "c": 4}}}}
        self.assertEqual(result, expected)

    def test_non_dict_override(self):
        """Test that non-dict values completely replace dict values."""
        defaults = {"a": {"x": 1, "y": 2}}
        override = {"a": "replaced"}
        result = merge(defaults, override)
        self.assertEqual(result, {"a": "replaced"})

    def test_dict_override_non_dict(self):
        """Test that dict values completely replace non-dict values."""
        defaults = {"a": "original"}
        override = {"a": {"x": 1, "y": 2}}
        result = merge(defaults, override)
        self.assertEqual(result, {"a": {"x": 1, "y": 2}})

    def test_none_values_in_override(self):
        """Test handling of None values in overrides."""
        defaults = {"a": 1, "b": 2}
        override = {"a": None, "c": None}
        result = merge(defaults, override)
        # None values should be preserved in result
        self.assertEqual(result, {"a": None, "b": 2, "c": None})

    def test_none_values_preserve_defaults(self):
        """Test that None values are properly handled."""
        defaults = {"a": 1}
        override = {"a": None}
        result = merge(defaults, override)
        self.assertEqual(result, {"a": None})

    def test_list_values(self):
        """Test merging with list values (should replace, not merge)."""
        defaults = {"a": [1, 2, 3]}
        override = {"a": [4, 5]}
        result = merge(defaults, override)
        self.assertEqual(result, {"a": [4, 5]})

    def test_mixed_types(self):
        """Test merging with mixed value types."""
        defaults = {"a": 1, "b": "string", "c": [1, 2], "d": {"nested": True}}
        override = {
            "a": "new",
            "b": 42,
            "c": {"replaced": True},
            "d": {"nested": False, "added": True},
        }
        result = merge(defaults, override)
        expected = {
            "a": "new",
            "b": 42,
            "c": {"replaced": True},
            "d": {"nested": False, "added": True},
        }
        self.assertEqual(result, expected)

    def test_original_not_modified(self):
        """Test that original dictionaries are not modified."""
        defaults = {"a": {"x": 1}}
        override = {"a": {"y": 2}}
        original_defaults = defaults.copy()
        original_override = override.copy()

        result = merge(defaults, override)

        # Original dictionaries should remain unchanged
        self.assertEqual(defaults, original_defaults)
        self.assertEqual(override, original_override)
        # But the result should contain the merged data
        self.assertEqual(result, {"a": {"x": 1, "y": 2}})

    def test_no_arguments_after_defaults(self):
        """Test merge with only defaults (no overrides)."""
        defaults = {"a": 1, "b": 2}
        result = merge(defaults)
        self.assertEqual(result, {"a": 1, "b": 2})
        # Should not modify the original
        self.assertIsNot(result, defaults)


if __name__ == "__main__":
    unittest.main()
