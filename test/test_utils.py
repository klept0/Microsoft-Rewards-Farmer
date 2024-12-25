import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from argparse import Namespace
from unittest import TestCase

from src.utils import Utils, sendNotification


class TestUtils(TestCase):
    def test_send_notification(self):
        Utils.args = Namespace()
        Utils.args.disable_apprise = False
        sendNotification("title", "body")
