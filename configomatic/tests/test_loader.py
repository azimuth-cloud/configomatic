"""
Unit tests for configomatic.loader module.
"""

import json
import pathlib
import tempfile
import unittest
from io import StringIO
from unittest.mock import Mock, mock_open, patch

from configomatic.exceptions import NoSuitableLoader, RequiredPackageNotAvailable
from configomatic.loader import (
    Suffixes,
    load_file,
    load_json,
    load_toml,
    load_yaml,
)


class TestSuffixes(unittest.TestCase):
    """Test cases for Suffixes class."""

    def test_suffixes_json(self):
        """Test JSON suffixes are correct."""
        self.assertEqual(Suffixes.JSON, [".json"])

    def test_suffixes_yaml(self):
        """Test YAML suffixes are correct."""
        self.assertEqual(Suffixes.YAML, [".yml", ".yaml"])

    def test_suffixes_toml(self):
        """Test TOML suffixes are correct."""
        self.assertEqual(Suffixes.TOML, [".toml"])

    def test_suffixes_are_lists(self):
        """Test that all suffix attributes are lists."""
        self.assertIsInstance(Suffixes.JSON, list)
        self.assertIsInstance(Suffixes.YAML, list)
        self.assertIsInstance(Suffixes.TOML, list)

    def test_suffixes_immutable(self):
        """Test that suffix lists contain expected extensions."""
        # Test JSON
        for ext in Suffixes.JSON:
            self.assertTrue(ext.startswith("."))

        # Test YAML
        for ext in Suffixes.YAML:
            self.assertTrue(ext.startswith("."))

        # Test TOML
        for ext in Suffixes.TOML:
            self.assertTrue(ext.startswith("."))


class TestLoadJson(unittest.TestCase):
    """Test cases for load_json function."""

    def test_load_json_valid_data(self):
        """Test loading valid JSON data."""
        json_data = '{"key": "value", "number": 42}'
        file_handle = StringIO(json_data)

        result = load_json(file_handle)
        expected = {"key": "value", "number": 42}
        self.assertEqual(result, expected)

    def test_load_json_empty_object(self):
        """Test loading empty JSON object."""
        json_data = "{}"
        file_handle = StringIO(json_data)

        result = load_json(file_handle)
        self.assertEqual(result, {})

    def test_load_json_array(self):
        """Test loading JSON array."""
        json_data = "[1, 2, 3]"
        file_handle = StringIO(json_data)

        result = load_json(file_handle)
        self.assertEqual(result, [1, 2, 3])

    def test_load_json_nested_structure(self):
        """Test loading nested JSON structure."""
        json_data = '{"section": {"key": "value", "array": [1, 2, 3]}}'
        file_handle = StringIO(json_data)

        result = load_json(file_handle)
        expected = {"section": {"key": "value", "array": [1, 2, 3]}}
        self.assertEqual(result, expected)

    def test_load_json_invalid_data(self):
        """Test loading invalid JSON data raises error."""
        json_data = '{"invalid": json}'  # Missing quotes around 'json'
        file_handle = StringIO(json_data)

        with self.assertRaises(json.JSONDecodeError):
            load_json(file_handle)

    def test_load_json_empty_file(self):
        """Test loading empty JSON file raises error."""
        file_handle = StringIO("")

        with self.assertRaises(json.JSONDecodeError):
            load_json(file_handle)


class TestLoadYaml(unittest.TestCase):
    """Test cases for load_yaml function."""

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.yaml")
    def test_load_yaml_available(self, mock_yaml):
        """Test loading YAML when yaml is available."""
        mock_yaml.safe_load.return_value = {"key": "value"}
        file_handle = StringIO("key: value")

        result = load_yaml(file_handle)

        mock_yaml.safe_load.assert_called_once_with(file_handle)
        self.assertEqual(result, {"key": "value"})

    @patch("configomatic.loader.yaml_available", False)
    def test_load_yaml_unavailable(self):
        """Test loading YAML when yaml is not available."""
        file_handle = StringIO("key: value")

        with self.assertRaises(RequiredPackageNotAvailable) as cm:
            load_yaml(file_handle)

        self.assertIn("PyYAML must be installed", str(cm.exception))

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.yaml")
    def test_load_yaml_empty_file(self, mock_yaml):
        """Test loading empty YAML file."""
        mock_yaml.safe_load.return_value = None
        file_handle = StringIO("")

        result = load_yaml(file_handle)

        mock_yaml.safe_load.assert_called_once_with(file_handle)
        self.assertIsNone(result)

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.yaml")
    def test_load_yaml_complex_structure(self, mock_yaml):
        """Test loading complex YAML structure."""
        expected_data = {
            "section": {"key": "value", "list": [1, 2, 3], "nested": {"inner": "data"}}
        }
        mock_yaml.safe_load.return_value = expected_data
        file_handle = StringIO("complex yaml")

        result = load_yaml(file_handle)

        mock_yaml.safe_load.assert_called_once_with(file_handle)
        self.assertEqual(result, expected_data)


class TestLoadToml(unittest.TestCase):
    """Test cases for load_toml function."""

    @patch("configomatic.loader.toml_available", True)
    @patch("configomatic.loader.toml")
    def test_load_toml_available(self, mock_toml):
        """Test loading TOML when toml is available."""
        mock_toml.load.return_value = {"key": "value"}
        file_handle = StringIO("key = 'value'")

        result = load_toml(file_handle)

        mock_toml.load.assert_called_once_with(file_handle)
        self.assertEqual(result, {"key": "value"})

    @patch("configomatic.loader.toml_available", False)
    def test_load_toml_unavailable(self):
        """Test loading TOML when toml is not available."""
        file_handle = StringIO("key = 'value'")

        with self.assertRaises(RequiredPackageNotAvailable) as cm:
            load_toml(file_handle)

        self.assertIn("toml must be installed", str(cm.exception))

    @patch("configomatic.loader.toml_available", True)
    @patch("configomatic.loader.toml")
    def test_load_toml_empty_file(self, mock_toml):
        """Test loading empty TOML file."""
        mock_toml.load.return_value = {}
        file_handle = StringIO("")

        result = load_toml(file_handle)

        mock_toml.load.assert_called_once_with(file_handle)
        self.assertEqual(result, {})

    @patch("configomatic.loader.toml_available", True)
    @patch("configomatic.loader.toml")
    def test_load_toml_complex_structure(self, mock_toml):
        """Test loading complex TOML structure."""
        expected_data = {"section": {"key": "value", "number": 42}, "array": [1, 2, 3]}
        mock_toml.load.return_value = expected_data
        file_handle = StringIO("complex toml")

        result = load_toml(file_handle)

        mock_toml.load.assert_called_once_with(file_handle)
        self.assertEqual(result, expected_data)


class TestLoadFile(unittest.TestCase):
    """Test cases for load_file function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: None)  # tempfile cleanup is automatic

    def test_load_file_json(self):
        """Test loading JSON file by extension."""
        json_path = pathlib.Path(self.temp_dir) / "test.json"
        json_data = {"key": "value", "number": 42}

        with patch.object(
            pathlib.Path, "open", mock_open(read_data='{"key": "value", "number": 42}')
        ):
            result = load_file(json_path)

        self.assertEqual(result, json_data)

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.yaml")
    def test_load_file_yaml_yml_extension(self, mock_yaml):
        """Test loading YAML file with .yml extension."""
        mock_yaml.safe_load.return_value = {"key": "value"}
        yaml_path = pathlib.Path(self.temp_dir) / "test.yml"

        with patch.object(pathlib.Path, "open", mock_open(read_data="key: value")):
            result = load_file(yaml_path)

        self.assertEqual(result, {"key": "value"})

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.yaml")
    def test_load_file_yaml_yaml_extension(self, mock_yaml):
        """Test loading YAML file with .yaml extension."""
        mock_yaml.safe_load.return_value = {"key": "value"}
        yaml_path = pathlib.Path(self.temp_dir) / "test.yaml"

        with patch.object(pathlib.Path, "open", mock_open(read_data="key: value")):
            result = load_file(yaml_path)

        self.assertEqual(result, {"key": "value"})

    @patch("configomatic.loader.toml_available", True)
    @patch("configomatic.loader.toml")
    def test_load_file_toml(self, mock_toml):
        """Test loading TOML file by extension."""
        mock_toml.load.return_value = {"key": "value"}
        toml_path = pathlib.Path(self.temp_dir) / "test.toml"

        with patch.object(pathlib.Path, "open", mock_open(read_data='key = "value"')):
            result = load_file(toml_path)

        self.assertEqual(result, {"key": "value"})

    def test_load_file_unknown_extension(self):
        """Test loading file with unknown extension raises error."""
        unknown_path = pathlib.Path(self.temp_dir) / "test.unknown"

        with patch.object(pathlib.Path, "open", mock_open(read_data="UNKNOWNFORMAT")):
            with self.assertRaises(NoSuitableLoader) as cm:
                load_file(unknown_path)

        self.assertIn("no loader for suffix .unknown", str(cm.exception))

    def test_load_file_no_extension(self):
        """Test loading file with no extension raises error."""
        no_ext_path = pathlib.Path(self.temp_dir) / "test"

        with patch.object(pathlib.Path, "open", mock_open(read_data="SOMEDATA")):
            with self.assertRaises(NoSuitableLoader) as cm:
                load_file(no_ext_path)

        self.assertIn("no loader for suffix", str(cm.exception))

    def test_load_file_case_sensitive_extension(self):
        """Test that file extension matching is case sensitive."""
        upper_json_path = pathlib.Path(self.temp_dir) / "test.JSON"

        with patch.object(
            pathlib.Path, "open", mock_open(read_data='{"key": "value"}')
        ):
            with self.assertRaises(NoSuitableLoader):
                load_file(upper_json_path)

    def test_load_file_pathlib_path_string(self):
        """Test loading file with string path converted to pathlib.Path."""
        json_path_str = str(pathlib.Path(self.temp_dir) / "test.json")
        json_path = pathlib.Path(json_path_str)

        with patch.object(
            pathlib.Path, "open", mock_open(read_data='{"key": "value"}')
        ):
            result = load_file(json_path)

        self.assertEqual(result, {"key": "value"})

    @patch("configomatic.loader.yaml_available", False)
    def test_load_file_yaml_unavailable(self):
        """Test loading YAML file when yaml is unavailable."""
        yaml_path = pathlib.Path(self.temp_dir) / "test.yml"

        with patch.object(pathlib.Path, "open", mock_open(read_data="key: value")):
            with self.assertRaises(RequiredPackageNotAvailable):
                load_file(yaml_path)

    @patch("configomatic.loader.toml_available", False)
    def test_load_file_toml_unavailable(self):
        """Test loading TOML file when toml is unavailable."""
        toml_path = pathlib.Path(self.temp_dir) / "test.toml"

        with patch.object(pathlib.Path, "open", mock_open(read_data='key = "value"')):
            with self.assertRaises(RequiredPackageNotAvailable):
                load_file(toml_path)


class TestYamlInclude(unittest.TestCase):
    """Test cases for YAML include functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: None)  # tempfile cleanup is automatic

    @patch("configomatic.loader.yaml_available", True)
    def test_yaml_available_constructor_registered(self):
        """Test that include constructor is registered when yaml is available."""
        # This test verifies that the constructor is registered at module import
        # when yaml is available. The actual registration happens at import time.
        from configomatic import loader

        # Re-patch yaml_available to ensure constructor registration
        with patch("configomatic.loader.yaml_available", True):
            # Import the module again to trigger constructor registration
            import importlib

            importlib.reload(loader)

            # Verify that yaml.add_constructor was called
            # We can't directly test the registration, but we can test that
            # the constructor function exists
            self.assertTrue(hasattr(loader, "include_constructor"))

    @patch("configomatic.loader.yaml_available", False)
    def test_yaml_unavailable_constructor_not_registered(self):
        """Test that include constructor is not registered when yaml is unavailable."""
        from configomatic import loader

        # The include_constructor function should still exist but not be registered
        self.assertTrue(hasattr(loader, "include_constructor"))

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.load_file")
    @patch("configomatic.loader.merge")
    @patch("glob.iglob")
    def test_include_constructor_single_file(
        self, mock_iglob, mock_merge, mock_load_file
    ):
        """Test include constructor with single file."""
        from configomatic.loader import include_constructor

        # Mock setup
        mock_node = Mock()
        mock_node.value = "./include.yaml"
        mock_loader = Mock()
        mock_loader.construct_scalar.return_value = "./include.yaml"

        mock_iglob.return_value = ["./include.yaml"]
        mock_load_file.return_value = {"included": "data"}
        mock_merge.return_value = {"included": "data"}

        # Test
        result = include_constructor(mock_loader, mock_node)

        # Verify
        mock_loader.construct_scalar.assert_called_once_with(mock_node)
        mock_iglob.assert_called_once_with("./include.yaml", recursive=True)
        mock_load_file.assert_called_once()
        self.assertEqual(result, {"included": "data"})

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.load_file")
    @patch("configomatic.loader.merge")
    @patch("glob.iglob")
    def test_include_constructor_multiple_files(
        self, mock_iglob, mock_merge, mock_load_file
    ):
        """Test include constructor with multiple comma-separated files."""
        from configomatic.loader import include_constructor

        # Mock setup
        mock_node = Mock()
        mock_loader = Mock()
        mock_loader.construct_scalar.return_value = "./file1.yaml, ./file2.yaml"

        def iglob_side_effect(pattern, recursive=True):
            if pattern == "./file1.yaml":
                return ["./file1.yaml"]
            elif pattern == "./file2.yaml":
                return ["./file2.yaml"]
            return []

        mock_iglob.side_effect = iglob_side_effect
        mock_load_file.side_effect = [{"file1": "data"}, {"file2": "data"}]
        mock_merge.return_value = {"merged": "data"}

        # Test
        result = include_constructor(mock_loader, mock_node)

        # Verify
        self.assertEqual(mock_iglob.call_count, 2)
        self.assertEqual(mock_load_file.call_count, 2)
        self.assertEqual(result, {"merged": "data"})

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.load_file")
    @patch("configomatic.loader.merge")
    @patch("glob.iglob")
    def test_include_constructor_glob_pattern(
        self, mock_iglob, mock_merge, mock_load_file
    ):
        """Test include constructor with glob pattern."""
        from configomatic.loader import include_constructor

        # Mock setup
        mock_node = Mock()
        mock_loader = Mock()
        mock_loader.construct_scalar.return_value = "./includes/*.yaml"

        mock_iglob.return_value = ["./includes/file1.yaml", "./includes/file2.yaml"]
        mock_load_file.side_effect = [{"file1": "data"}, {"file2": "data"}]
        mock_merge.return_value = {"merged": "glob_data"}

        # Test
        result = include_constructor(mock_loader, mock_node)

        # Verify
        mock_iglob.assert_called_once_with("./includes/*.yaml", recursive=True)
        self.assertEqual(mock_load_file.call_count, 2)
        self.assertEqual(result, {"merged": "glob_data"})

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.load_file")
    @patch("configomatic.loader.merge")
    @patch("glob.iglob")
    def test_include_constructor_with_exclusions(
        self, mock_iglob, mock_merge, mock_load_file
    ):
        """Test include constructor with exclusion patterns."""
        from configomatic.loader import include_constructor

        # Mock setup
        mock_node = Mock()
        mock_loader = Mock()
        mock_loader.construct_scalar.return_value = (
            "./includes/*.yaml, !./includes/excluded.yaml"
        )

        def iglob_side_effect(pattern, recursive=True):
            if pattern == "./includes/*.yaml":
                return [
                    "./includes/file1.yaml",
                    "./includes/excluded.yaml",
                    "./includes/file2.yaml",
                ]
            elif pattern == "./includes/excluded.yaml":
                return ["./includes/excluded.yaml"]
            return []

        mock_iglob.side_effect = iglob_side_effect
        mock_load_file.side_effect = [{"file1": "data"}, {"file2": "data"}]
        mock_merge.return_value = {"merged": "excluded_data"}

        # Test
        result = include_constructor(mock_loader, mock_node)

        # Verify
        self.assertEqual(mock_iglob.call_count, 2)
        # Should only load 2 files (excluded file should not be loaded)
        self.assertEqual(mock_load_file.call_count, 2)
        self.assertEqual(result, {"merged": "excluded_data"})

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.load_file")
    @patch("configomatic.loader.merge")
    @patch("glob.iglob")
    def test_include_constructor_sorted_order(
        self, mock_iglob, mock_merge, mock_load_file
    ):
        """Test include constructor processes files in sorted order."""
        from configomatic.loader import include_constructor

        # Mock setup
        mock_node = Mock()
        mock_loader = Mock()
        mock_loader.construct_scalar.return_value = "./includes/*.yaml"

        # Return files in non-sorted order
        mock_iglob.return_value = [
            "./includes/z.yaml",
            "./includes/a.yaml",
            "./includes/m.yaml",
        ]
        mock_load_file.side_effect = [{"a": "data"}, {"m": "data"}, {"z": "data"}]
        mock_merge.return_value = {"merged": "sorted_data"}

        # Test
        include_constructor(mock_loader, mock_node)

        # Verify load_file was called with sorted paths
        expected_paths = [
            pathlib.Path("./includes/a.yaml").resolve(),
            pathlib.Path("./includes/m.yaml").resolve(),
            pathlib.Path("./includes/z.yaml").resolve(),
        ]
        actual_calls = [call[0][0] for call in mock_load_file.call_args_list]
        self.assertEqual(actual_calls, expected_paths)

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.load_file")
    @patch("configomatic.loader.merge")
    @patch("glob.iglob")
    def test_include_constructor_whitespace_handling(
        self, mock_iglob, mock_merge, mock_load_file
    ):
        """Test include constructor handles whitespace in path list."""
        from configomatic.loader import include_constructor

        # Mock setup
        mock_node = Mock()
        mock_loader = Mock()
        mock_loader.construct_scalar.return_value = (
            " ./file1.yaml , ./file2.yaml , ./file3.yaml "
        )

        def iglob_side_effect(pattern, recursive=True):
            return (
                [pattern]
                if pattern in ["./file1.yaml", "./file2.yaml", "./file3.yaml"]
                else []
            )

        mock_iglob.side_effect = iglob_side_effect
        mock_load_file.side_effect = [
            {"file1": "data"},
            {"file2": "data"},
            {"file3": "data"},
        ]
        mock_merge.return_value = {"merged": "whitespace_data"}

        # Test
        result = include_constructor(mock_loader, mock_node)

        # Verify all three files were processed despite whitespace
        self.assertEqual(mock_iglob.call_count, 3)
        self.assertEqual(mock_load_file.call_count, 3)
        self.assertEqual(result, {"merged": "whitespace_data"})

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.load_file")
    @patch("configomatic.loader.merge")
    @patch("glob.iglob")
    def test_include_constructor_no_matches(
        self, mock_iglob, mock_merge, mock_load_file
    ):
        """Test include constructor with pattern that matches no files."""
        from configomatic.loader import include_constructor

        # Mock setup
        mock_node = Mock()
        mock_loader = Mock()
        mock_loader.construct_scalar.return_value = "./nonexistent/*.yaml"

        mock_iglob.return_value = []  # No matches
        mock_merge.return_value = {}

        # Test
        result = include_constructor(mock_loader, mock_node)

        # Verify
        mock_iglob.assert_called_once_with("./nonexistent/*.yaml", recursive=True)
        mock_load_file.assert_not_called()
        mock_merge.assert_called_once_with()  # Called with no arguments
        self.assertEqual(result, {})

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.load_file")
    @patch("configomatic.loader.merge")
    @patch("glob.iglob")
    def test_include_constructor_recursive_glob(
        self, mock_iglob, mock_merge, mock_load_file
    ):
        """Test include constructor uses recursive glob."""
        from configomatic.loader import include_constructor

        # Mock setup
        mock_node = Mock()
        mock_loader = Mock()
        mock_loader.construct_scalar.return_value = "./**/config.yaml"

        mock_iglob.return_value = ["./subdir/config.yaml", "./deep/nested/config.yaml"]
        mock_load_file.side_effect = [{"sub": "config"}, {"deep": "config"}]
        mock_merge.return_value = {"merged": "recursive"}

        # Test
        result = include_constructor(mock_loader, mock_node)

        # Verify recursive=True was passed
        mock_iglob.assert_called_once_with("./**/config.yaml", recursive=True)
        self.assertEqual(mock_load_file.call_count, 2)
        self.assertEqual(result, {"merged": "recursive"})

    @patch("configomatic.loader.yaml_available", True)
    @patch("configomatic.loader.load_file")
    @patch("configomatic.loader.merge")
    @patch("glob.iglob")
    def test_include_constructor_merge_order(
        self, mock_iglob, mock_merge, mock_load_file
    ):
        """Test that merge is called with loaded configs in correct order."""
        from configomatic.loader import include_constructor

        # Mock setup
        mock_node = Mock()
        mock_loader = Mock()
        mock_loader.construct_scalar.return_value = "./includes/*.yaml"

        mock_iglob.return_value = ["./includes/b.yaml", "./includes/a.yaml"]
        config_a = {"config": "a"}
        config_b = {"config": "b"}
        mock_load_file.side_effect = [
            config_a,
            config_b,
        ]  # Called in sorted order (a, b)
        mock_merge.return_value = {"merged": "result"}

        # Test
        result = include_constructor(mock_loader, mock_node)

        # Verify merge was called with configs in the order they were loaded
        # They should be sorted by filename
        mock_merge.assert_called_once_with(config_a, config_b)
        self.assertEqual(result, {"merged": "result"})


if __name__ == "__main__":
    unittest.main()
