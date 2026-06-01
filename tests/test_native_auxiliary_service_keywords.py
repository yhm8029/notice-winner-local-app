from __future__ import annotations

import unittest

from backend.services.native_gui_rules import is_auxiliary_service_project


class NativeAuxiliaryServiceKeywordTests(unittest.TestCase):
    def test_auxiliary_service_keywords_cover_evaluation_maintenance_and_operation_titles(self) -> None:
        titles = [
            "\uc124\uacc4\uacf5\ubaa8 \uc81c\uc548\uc11c \ud3c9\uac00\uc6a9\uc5ed",
            "\uc124\uacc4\uacf5\ubaa8 \uc81c\uc548\uc11c \ud3c9\uac00 \uc6a9\uc5ed",
            "\uc124\uacc4\uacf5\ubaa8 \ud648\ud398\uc774\uc9c0 \uc0c1\uc6a9SW \uc720\uc9c0\ubcf4\uc218\uc6a9\uc5ed",
            "\uc124\uacc4\uacf5\ubaa8 \ud648\ud398\uc774\uc9c0 \uc0c1\uc6a9SW \uc720\uc9c0\ubcf4\uc218",
            "\ub300\ud55c\ubbfc\uad6d \ub3c4\uc2dc\uc232 \uc124\uacc4 \uacf5\ubaa8\ub300\uc804 \uc6b4\uc601",
            "\uc124\uacc4 \uacf5\ubaa8\uc804 \uc6b4\uc601",
            "\uc2dc\uc0c1\uc2dd \uc6b4\uc601 \uc6a9\uc5ed",
        ]

        for title in titles:
            with self.subTest(title=title):
                self.assertTrue(is_auxiliary_service_project(title))

    def test_auxiliary_service_keywords_cover_broadcast_manual_and_review_system_titles(self) -> None:
        titles = [
            "2024\ub144\ub3c4 \uac74\ucd95 \uc124\uacc4\uacf5\ubaa8 \uc2ec\uc0ac\uc704\uc6d0\ud68c \uc2ec\uc0ac \uc911\uacc4 \ubc0f \uc1a1\ucd9c \uc6a9\uc5ed",
            "\uc11c\uc6b8\uc2dd\ubb3c\uc6d0 \uc2dd\uc7ac\uc124\uacc4\uacf5\ubaa8\uc804 \uc815\uc6d0\uc870\uc131 \ub9e4\ub274\uc5bc \uc81c\uc791 \uc6a9\uc5ed",
            "\uacbd\uae30\ub3c4\uad50\uc721\uccad \uc124\uacc4\uacf5\ubaa8 \uc2ec\uc0ac\uc2dc\uc2a4\ud15c \uace0\ub3c4\ud654(2\ucc28) \uc6a9\uc5ed \uc804\uc790\uc218\uc758\uc2dc\ub2f4",
            "\uc778\ucc9c\uad11\uc5ed\uc2dc\uad50\uc721\uccad \uc124\uacc4\uacf5\ubaa8 \uc2ec\uc0ac\uc2dc\uc2a4\ud15c \uad6c\ucd95 \uc6a9\uc5ed",
        ]

        for title in titles:
            with self.subTest(title=title):
                self.assertTrue(is_auxiliary_service_project(title))

    def test_auxiliary_service_keywords_cover_management_software_and_operation_titles(self) -> None:
        titles = [
            "\uad11\uc8fc\ube44\uc5d4\ub0a0\ub808\uc804\uc2dc\uad00 \uac74\ub9bd \uac74\ucd95\uae30\ud68d \ubc0f \uc124\uacc4\uacf5\ubaa8 \uad00\ub9ac-\uc785\ucc30",
            "\uad11\uc8fc\ube44\uc5d4\ub0a0\ub808\uc804\uc2dc\uad00 \uac74\ub9bd \uac74\ucd95\uae30\ud68d \ubc0f \uc124\uacc4\uacf5\ubaa8 \uad00\ub9ac",
            "\uc124\uacc4\uacf5\ubaa8 \ud648\ud398\uc774\uc9c0 \uc774\uad00 \ubc0f \uc7ac\uad6c\ucd95 \uc6a9\uc5ed \uc785\ucc30 \uacf5\uace0",
            "\uac10\ud638\uc9c0\uad6c \uac70\uc810\uc2dc\uc124 \uac74\ucd95\uc124\uacc4\uacf5\ubaa8 \ubc0f \uc2dc\ubbfc \uc544\uc774\ub514\uc5b4 \ub9ac\ube59\ub7a9 \uc6b4\uc601 \uc704\ud0c1 \uc6a9\uc5ed",
        ]

        for title in titles:
            with self.subTest(title=title):
                self.assertTrue(is_auxiliary_service_project(title))


if __name__ == "__main__":
    unittest.main()
