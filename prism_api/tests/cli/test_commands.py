import unittest
from unittest import mock

import pytest
from click.testing import CliRunner

from ..mocks import rexflow_api as rexflow
from prism_api.cli.commands import (
    cancel_workflows,
    refresh_workflows,
)


@pytest.mark.ci
@mock.patch('prism_api.cli.commands.rexflow', rexflow)
@mock.patch('prism_api.cli.commands.settings.DEBUG', True)
class TestCommands(unittest.TestCase):
    def test_cancel_workflows(self):
        runner = CliRunner()
        result = runner.invoke(cancel_workflows)
        self.assertEqual(result.exit_code, 0)

    def test_refresh_workflows(self):
        runner = CliRunner()
        result = runner.invoke(refresh_workflows)
        self.assertEqual(result.exit_code, 0)
