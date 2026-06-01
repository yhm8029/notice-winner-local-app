from __future__ import annotations

import unittest

from backend.services.synap_text_extract import extract_synap_page_text
from backend.services.synap_text_extract import extract_synap_viewer_key


class SynapTextExtractTests(unittest.TestCase):
    def test_extract_synap_viewer_key_reads_query_parameter(self) -> None:
        viewer_url = (
            "https://www.g2b.go.kr/SynapDocViewServer/viewer/doc.html"
            "?key=abc123&convType=img&convLocale=ko_KR"
        )
        self.assertEqual("abc123", extract_synap_viewer_key(viewer_url))

    def test_extract_synap_page_text_joins_paragraph_text_nodes(self) -> None:
        xml_text = """<?xml version="1.0" encoding="UTF-8" ?>
<document>
  <page w="794" h="1123">
    <paragraph l="0" t="0" w="100" h="20">
      <text l="0" t="0" w="10" h="20">문</text>
      <text l="10" t="0" w="10" h="20">의</text>
      <text l="20" t="0" w="10" h="20">:</text>
      <text l="30" t="0" w="10" h="20"> </text>
      <text l="40" t="0" w="10" h="20">건</text>
      <text l="50" t="0" w="10" h="20">축</text>
      <text l="60" t="0" w="10" h="20">과</text>
      <text l="70" t="0" w="10" h="20"> </text>
      <text l="80" t="0" w="10" h="20">0</text>
      <text l="90" t="0" w="10" h="20">2</text>
      <text l="100" t="0" w="10" h="20">-</text>
      <text l="110" t="0" w="10" h="20">1</text>
      <text l="120" t="0" w="10" h="20">2</text>
      <text l="130" t="0" w="10" h="20">3</text>
      <text l="140" t="0" w="10" h="20">4</text>
    </paragraph>
    <paragraph l="0" t="20" w="100" h="20">
      <text l="0" t="20" w="10" h="20">연</text>
      <text l="10" t="20" w="10" h="20">면</text>
      <text l="20" t="20" w="10" h="20">적</text>
      <text l="30" t="20" w="10" h="20"> </text>
      <text l="40" t="20" w="10" h="20">1</text>
      <text l="50" t="20" w="10" h="20">,</text>
      <text l="60" t="20" w="10" h="20">2</text>
      <text l="70" t="20" w="10" h="20">3</text>
      <text l="80" t="20" w="10" h="20">4</text>
      <text l="90" t="20" w="10" h="20">㎡</text>
    </paragraph>
  </page>
</document>"""
        self.assertEqual("문의: 건축과 02-1234\n연면적 1,234㎡", extract_synap_page_text(xml_text))


if __name__ == "__main__":
    unittest.main()
