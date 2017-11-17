# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from MarieClaire.content.testing import MARIECLAIRE_CONTENT_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that MarieClaire.content is properly installed."""

    layer = MARIECLAIRE_CONTENT_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if MarieClaire.content is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'MarieClaire.content'))

    def test_browserlayer(self):
        """Test that IMarieclaireContentLayer is registered."""
        from MarieClaire.content.interfaces import (
            IMarieclaireContentLayer)
        from plone.browserlayer import utils
        self.assertIn(IMarieclaireContentLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = MARIECLAIRE_CONTENT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        self.installer.uninstallProducts(['MarieClaire.content'])

    def test_product_uninstalled(self):
        """Test if MarieClaire.content is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'MarieClaire.content'))

    def test_browserlayer_removed(self):
        """Test that IMarieclaireContentLayer is removed."""
        from MarieClaire.content.interfaces import \
            IMarieclaireContentLayer
        from plone.browserlayer import utils
        self.assertNotIn(IMarieclaireContentLayer, utils.registered_layers())
