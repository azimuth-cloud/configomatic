"""
Unit tests for configomatic.configuration module.
"""

import pathlib
import tempfile
import typing as t
import unittest
from unittest.mock import patch

from pydantic import BaseModel

from configomatic.configuration import (
    ConfigEnvironmentDict,
    Configuration,
    ConfigurationMeta,
    Section,
)
from configomatic.exceptions import FileNotFound


class TestSection(unittest.TestCase):
    """Test cases for Section class."""

    def test_section_inheritance(self):
        """Test that Section inherits from BaseModel."""
        self.assertTrue(issubclass(Section, BaseModel))

    def test_alias_generator(self):
        """Test that Section uses snake_to_pascal alias generator."""

        class TestSection(Section):
            test_field: str

        section = TestSection(testField="value")
        self.assertEqual(section.test_field, "value")

    def test_populate_by_name(self):
        """Test that Section supports both alias and field names."""

        class TestSection(Section):
            test_field: str

        # Test with snake_case field name
        section1 = TestSection(test_field="value1")
        self.assertEqual(section1.test_field, "value1")

        # Test with pascalCase alias
        section2 = TestSection(testField="value2")
        self.assertEqual(section2.test_field, "value2")

    def test_section_serialization(self):
        """Test Section serialization uses aliases."""

        class TestSection(Section):
            test_field: str
            another_field: int = 42

        section = TestSection(test_field="value")
        data = section.model_dump(by_alias=True)
        expected = {"testField": "value", "anotherField": 42}
        self.assertEqual(data, expected)

    def test_section_complex_field_names(self):
        """Test Section with complex field names."""

        class TestSection(Section):
            http_status_code: int
            api_key_secret: str

        section = TestSection(httpStatusCode=200, apiKeySecret="secret")
        self.assertEqual(section.http_status_code, 200)
        self.assertEqual(section.api_key_secret, "secret")


class TestConfigEnvironmentDict(unittest.TestCase):
    """Test cases for ConfigEnvironmentDict TypedDict."""

    def test_config_environment_dict_structure(self):
        """Test ConfigEnvironmentDict structure and type annotations."""
        # Test that all expected fields are present with correct types
        annotations = ConfigEnvironmentDict.__annotations__
        expected_fields = {
            "path_env_var": str | None,
            "default_path": str | None,
            "load_file": t.Callable[[str], dict[str, t.Any]] | None,
            "env_prefix": str | None,
        }
        self.assertEqual(annotations, expected_fields)

    def test_config_environment_dict_total_false(self):
        """Test that ConfigEnvironmentDict has total=False."""
        # All fields should be optional
        config_env = ConfigEnvironmentDict()
        self.assertEqual(config_env, {})

    def test_config_environment_dict_creation(self):
        """Test creation of ConfigEnvironmentDict with various fields."""

        def mock_loader(path: str) -> dict[str, t.Any]:
            return {"loaded": True}

        config_env = ConfigEnvironmentDict(
            path_env_var="CONFIG_PATH",
            default_path="/default/config.yml",
            load_file=mock_loader,
            env_prefix="MYAPP",
        )

        self.assertEqual(config_env["path_env_var"], "CONFIG_PATH")
        self.assertEqual(config_env["default_path"], "/default/config.yml")
        self.assertEqual(config_env["load_file"], mock_loader)
        self.assertEqual(config_env["env_prefix"], "MYAPP")


class TestConfigurationMeta(unittest.TestCase):
    """
    Test cases for ConfigurationMeta metaclass behavior through Configuration
    inheritance.
    """

    def test_configuration_meta_inheritance(self):
        """Test that ConfigurationMeta inherits from BaseModel metaclass."""
        self.assertTrue(issubclass(ConfigurationMeta, type(BaseModel)))

    def test_config_env_inheritance_from_bases(self):
        """Test that config_env is inherited from base classes."""

        class BaseConfig(Configuration):
            config_env = ConfigEnvironmentDict(
                path_env_var="BASE_CONFIG_PATH",
                default_path="/base/config.yml",
            )

        class ChildConfig(BaseConfig):
            pass

        child = ChildConfig(_use_file=False, _use_env=False)
        self.assertEqual(child.config_env["path_env_var"], "BASE_CONFIG_PATH")
        self.assertEqual(child.config_env["default_path"], "/base/config.yml")

    def test_config_env_override_in_child(self):
        """Test that child config_env overrides parent config_env."""

        class BaseConfig(Configuration):
            config_env = ConfigEnvironmentDict(
                path_env_var="BASE_CONFIG_PATH",
                default_path="/base/config.yml",
            )

        class ChildConfig(BaseConfig):
            config_env = ConfigEnvironmentDict(
                path_env_var="CHILD_CONFIG_PATH",
                env_prefix="CHILD",
            )

        child = ChildConfig(_use_file=False, _use_env=False)
        self.assertEqual(child.config_env["path_env_var"], "CHILD_CONFIG_PATH")
        self.assertEqual(child.config_env["env_prefix"], "CHILD")
        # default_path should be inherited from base
        self.assertEqual(child.config_env["default_path"], "/base/config.yml")

    def test_config_env_from_kwargs(self):
        """Test that config_env can be set from class creation kwargs."""

        class TestConfig(
            Configuration,
            path_env_var="KWARGS_PATH",
            env_prefix="KWARGS",
        ):
            pass

        config = TestConfig(_use_file=False, _use_env=False)
        self.assertEqual(config.config_env["path_env_var"], "KWARGS_PATH")
        self.assertEqual(config.config_env["env_prefix"], "KWARGS")

    def test_config_env_classvar_annotation(self):
        """Test that config_env has ClassVar annotation."""
        # Check that config_env is annotated as ClassVar
        annotations = Configuration.__annotations__
        self.assertIn("config_env", annotations)
        # The annotation should be ClassVar[ConfigEnvironmentDict]
        expected_annotation = t.ClassVar[ConfigEnvironmentDict]
        self.assertEqual(annotations["config_env"], expected_annotation)

    def test_pydantic_kwargs_passthrough(self):
        """Test that non-config_env kwargs are passed to Pydantic."""

        class TestConfig(Configuration, validate_default=True):
            test_field: str = "default"

        # Should not raise an error during class creation
        config = TestConfig(_use_file=False, _use_env=False)
        self.assertEqual(config.test_field, "default")


class TestConfiguration(unittest.TestCase):
    """Test cases for Configuration class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: None)  # tempfile cleanup is automatic

    def test_configuration_inheritance(self):
        """Test that Configuration inherits from BaseModel."""
        self.assertTrue(issubclass(Configuration, BaseModel))

    def test_configuration_uses_snake_to_pascal(self):
        """Test that Configuration uses snake_to_pascal alias generator."""

        class TestConfig(Configuration):
            test_field: str

        config = TestConfig(testField="value", _use_file=False, _use_env=False)
        self.assertEqual(config.test_field, "value")

    def test_configuration_populate_by_name(self):
        """Test that Configuration supports both alias and field names."""

        class TestConfig(Configuration):
            test_field: str

        config1 = TestConfig(test_field="value1", _use_file=False, _use_env=False)
        config2 = TestConfig(testField="value2", _use_file=False, _use_env=False)
        self.assertEqual(config1.test_field, "value1")
        self.assertEqual(config2.test_field, "value2")

    def test_init_with_defaults(self):
        """Test Configuration initialization with default parameters."""

        class TestConfig(Configuration):
            test_field: str = "default"

        with (
            patch.object(TestConfig, "_load_file", return_value={}),
            patch.object(TestConfig, "_load_environ", return_value={}),
        ):
            config = TestConfig()
            self.assertEqual(config.test_field, "default")

    def test_init_use_file_false(self):
        """Test Configuration with _use_file=False."""

        class TestConfig(Configuration):
            test_field: str = "default"

        with (
            patch.object(TestConfig, "_load_file") as mock_load_file,
            patch.object(TestConfig, "_load_environ", return_value={}),
        ):
            config = TestConfig(_use_file=False)
            mock_load_file.assert_not_called()
            self.assertEqual(config.test_field, "default")

    def test_init_use_env_false(self):
        """Test Configuration with _use_env=False."""

        class TestConfig(Configuration):
            test_field: str = "default"

        with (
            patch.object(TestConfig, "_load_file", return_value={}),
            patch.object(TestConfig, "_load_environ") as mock_load_environ,
        ):
            config = TestConfig(_use_env=False)
            mock_load_environ.assert_not_called()
            self.assertEqual(config.test_field, "default")

    def test_init_with_path(self):
        """Test Configuration with explicit _path."""

        class TestConfig(Configuration):
            test_field: str = "default"

        with (
            patch.object(TestConfig, "_load_file", return_value={}) as mock_load_file,
            patch.object(TestConfig, "_load_environ", return_value={}),
        ):
            config = TestConfig(_path="/custom/path.yml")
            mock_load_file.assert_called_once_with("/custom/path.yml")
            self.assertEqual(config.test_field, "default")

    def test_init_kwargs_override(self):
        """Test that init_kwargs have highest precedence."""

        class TestConfig(Configuration):
            test_field: str
            another_field: int = 10

        with (
            patch.object(
                TestConfig,
                "_load_file",
                return_value={"test_field": "file", "another_field": 20},
            ),
            patch.object(
                TestConfig,
                "_load_environ",
                return_value={"test_field": "env", "another_field": 30},
            ),
        ):
            config = TestConfig(test_field="init", another_field=40)
            self.assertEqual(config.test_field, "init")
            self.assertEqual(config.another_field, 40)

    def test_config_precedence_order(self):
        """Test that configuration precedence is: file < env < init_kwargs."""

        class TestConfig(Configuration):
            field_a: str
            field_b: str
            field_c: str

        with (
            patch.object(
                TestConfig,
                "_load_file",
                return_value={
                    "field_a": "file_a",
                    "field_b": "file_b",
                    "field_c": "file_c",
                },
            ),
            patch.object(
                TestConfig,
                "_load_environ",
                return_value={"field_b": "env_b", "field_c": "env_c"},
            ),
        ):
            config = TestConfig(field_c="init_c")
            self.assertEqual(config.field_a, "file_a")  # Only in file
            self.assertEqual(config.field_b, "env_b")  # File overridden by env
            self.assertEqual(config.field_c, "init_c")  # Env overridden by init

    def test_load_file_from_env_var(self):
        """Test loading file path from environment variable."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(path_env_var="CONFIG_PATH")

        config = TestConfig(_use_env=False)

        with (
            patch("os.environ", {"CONFIG_PATH": "/env/config.yml"}),
            patch.object(pathlib.Path, "is_file", return_value=True),
            patch(
                "configomatic.configuration.default_load_file",
                return_value={"loaded": True},
            ),
        ):
            result = config._load_file(None)
            self.assertEqual(result, {"loaded": True})

    def test_load_file_explicit_path(self):
        """Test loading file with explicit path."""

        class TestConfig(Configuration):
            pass

        config = TestConfig(_use_file=False, _use_env=False)

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "configomatic.configuration.default_load_file",
                return_value={"explicit": True},
            ),
        ):
            result = config._load_file("/explicit/path.yml")
            self.assertEqual(result, {"explicit": True})

    def test_load_file_default_path(self):
        """Test loading file with default path."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(default_path="/default/config.yml")

        config = TestConfig(_use_file=False, _use_env=False)

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "configomatic.configuration.default_load_file",
                return_value={"default": True},
            ),
        ):
            result = config._load_file(None)
            self.assertEqual(result, {"default": True})

    def test_load_file_no_path(self):
        """Test loading file when no path is available."""

        class TestConfig(Configuration):
            pass

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_file(None)
        self.assertEqual(result, {})

    def test_load_file_explicit_path_not_found(self):
        """Test loading file with explicit path that doesn't exist."""

        class TestConfig(Configuration):
            pass

        config = TestConfig(_use_file=False, _use_env=False)

        with patch("pathlib.Path.is_file", return_value=False):
            with self.assertRaises(FileNotFound) as cm:
                config._load_file("/explicit/missing.yml")
            self.assertIn("does not exist", str(cm.exception))

    def test_load_file_default_path_not_found(self):
        """Test loading file with default path that doesn't exist (should not raise)."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(default_path="/default/missing.yml")

        config = TestConfig(_use_file=False, _use_env=False)

        with patch("pathlib.Path.is_file", return_value=False):
            result = config._load_file(None)
            self.assertEqual(result, {})

    def test_load_file_custom_loader(self):
        """Test loading file with custom load_file function."""

        def custom_loader(path):
            return {"custom": "loaded", "path": str(path)}

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(load_file=custom_loader)

        config = TestConfig(_use_file=False, _use_env=False)

        with patch("pathlib.Path.is_file", return_value=True):
            result = config._load_file("/custom/path.yml")
            expected = {
                "custom": "loaded",
                "path": str(pathlib.Path("/custom/path.yml")),
            }
            self.assertEqual(result, expected)

    def test_load_file_loader_returns_none(self):
        """Test loading file when loader returns None."""

        def none_loader(path):
            return None

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(load_file=none_loader)

        config = TestConfig(_use_file=False, _use_env=False)

        with patch("pathlib.Path.is_file", return_value=True):
            result = config._load_file("/path.yml")
            self.assertEqual(result, {})

    @patch("os.environ", {})
    def test_load_environ_empty(self):
        """Test loading environment variables with empty environment."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(env_prefix="TEST")

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        self.assertEqual(result, {})

    @patch("os.environ", {"TEST__FIELD": "value"})
    def test_load_environ_simple(self):
        """Test loading simple environment variable."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(env_prefix="TEST")

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        self.assertEqual(result, {"field": "value"})

    @patch(
        "os.environ",
        {
            "TEST__FIELD_A": "value_a",
            "TEST__FIELD_B": "value_b",
        },
    )
    def test_load_environ_multiple_fields(self):
        """Test loading multiple environment variables."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(env_prefix="TEST")

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        expected = {
            "field_a": "value_a",
            "field_b": "value_b",
        }
        self.assertEqual(result, expected)

    @patch("os.environ", {"TEST__SECTION__FIELD": "nested_value"})
    def test_load_environ_nested(self):
        """Test loading nested environment variables."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(env_prefix="TEST")

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        self.assertEqual(result, {"section": {"field": "nested_value"}})

    @patch(
        "os.environ",
        {
            "TEST__SECTION__FIELD_A": "value_a",
            "TEST__SECTION__FIELD_B": "value_b",
            "TEST__OTHER__FIELD": "other_value",
        },
    )
    def test_load_environ_complex_nesting(self):
        """Test loading complex nested environment variables."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(env_prefix="TEST")

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        expected = {
            "section": {
                "field_a": "value_a",
                "field_b": "value_b",
            },
            "other": {
                "field": "other_value",
            },
        }
        self.assertEqual(result, expected)

    @patch("os.environ", {"FIELD": "no_prefix_value"})
    def test_load_environ_no_prefix(self):
        """Test loading environment variables without prefix."""

        class TestConfig(Configuration):
            pass  # No env_prefix set

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        self.assertEqual(result, {"field": "no_prefix_value"})

    @patch(
        "os.environ",
        {
            "TEST__FIELD": "value",
            "OTHER__FIELD": "ignored",
            "NO_PREFIX": "ignored",
        },
    )
    def test_load_environ_prefix_filtering(self):
        """Test that only variables with correct prefix are loaded."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(env_prefix="TEST")

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        self.assertEqual(result, {"field": "value"})

    @patch(
        "os.environ",
        {
            "TEST__FIELD": "",
            "TEST__OTHER": "value",
        },
    )
    def test_load_environ_empty_values_ignored(self):
        """Test that empty environment variables are ignored."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(env_prefix="TEST")

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        self.assertEqual(result, {"other": "value"})

    @patch("os.environ", {"test__field": "lowercase"})
    def test_load_environ_case_insensitive_prefix(self):
        """Test that prefix matching is case insensitive."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(env_prefix="TEST")

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        self.assertEqual(result, {"field": "lowercase"})

    @patch("os.environ", {"TEST__FIELD_NAME": "value"})
    def test_load_environ_field_names_lowercase(self):
        """Test that field names are converted to lowercase."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(env_prefix="TEST")

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        self.assertEqual(result, {"field_name": "value"})

    @patch("os.environ", {"TEST__SECTION__DEEPLY__NESTED__FIELD": "deep_value"})
    def test_load_environ_deep_nesting(self):
        """Test loading deeply nested environment variables."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(env_prefix="TEST")

        config = TestConfig(_use_file=False, _use_env=False)
        result = config._load_environ()
        expected = {"section": {"deeply": {"nested": {"field": "deep_value"}}}}
        self.assertEqual(result, expected)

    def test_integration_all_sources(self):
        """Test integration of file, environment, and init_kwargs together."""

        class TestConfig(Configuration):
            config_env = ConfigEnvironmentDict(
                default_path="/default/config.yml",
                env_prefix="TEST",
            )
            field_a: str
            field_b: str
            field_c: str
            field_d: str

        file_config = {
            "field_a": "from_file",
            "field_b": "from_file",
            "field_c": "from_file",
            "field_d": "from_file",
        }
        env_config = {"field_b": "from_env", "field_c": "from_env"}

        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "configomatic.configuration.default_load_file", return_value=file_config
            ),
            patch.object(TestConfig, "_load_environ", return_value=env_config),
        ):
            config = TestConfig(field_c="from_init")

            self.assertEqual(config.field_a, "from_file")  # Only in file
            self.assertEqual(config.field_b, "from_env")  # File overridden by env
            self.assertEqual(config.field_c, "from_init")  # Env overridden by init
            self.assertEqual(config.field_d, "from_file")  # Only in file

    def test_configuration_with_section_fields(self):
        """Test Configuration with Section fields."""

        class DatabaseSection(Section):
            host: str
            port: int = 5432

        class TestConfig(Configuration):
            database: DatabaseSection
            app_name: str = "test"

        with (
            patch.object(TestConfig, "_load_file", return_value={}),
            patch.object(TestConfig, "_load_environ", return_value={}),
        ):
            config = TestConfig(database={"host": "localhost", "port": 3306})

            self.assertIsInstance(config.database, DatabaseSection)
            self.assertEqual(config.database.host, "localhost")
            self.assertEqual(config.database.port, 3306)
            self.assertEqual(config.app_name, "test")

    def test_error_handling_during_merge(self):
        """Test error handling when merge fails."""

        class TestConfig(Configuration):
            field: str

        # Test with invalid merge data
        with (
            patch.object(TestConfig, "_load_file", return_value={}),
            patch.object(TestConfig, "_load_environ", return_value={}),
            patch(
                "configomatic.configuration.merge",
                side_effect=Exception("Merge failed"),
            ),
        ):
            with self.assertRaises(Exception) as cm:
                TestConfig()
            self.assertIn("Merge failed", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
