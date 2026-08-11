import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PluginContractTests(unittest.TestCase):
    def test_plugin_entry_is_valid_python(self):
        ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))

    def test_metadata_and_agent_tool_are_present(self):
        metadata = (ROOT / "metadata.yaml").read_text(encoding="utf-8")
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("name: astrbot_plugin_nowhere", metadata)
        self.assertIn('astrbot_version: ">=4.17,<5"', metadata)
        self.assertIn('@filter.llm_tool(name="nowhere_travel")', source)
        self.assertNotIn("register_llm_tool", source)

    def test_upstream_runtime_and_data_are_vendored(self):
        server = ROOT / "vendor" / "nowhere" / "server.py"
        self.assertTrue(server.is_file())
        source = server.read_text(encoding="utf-8")
        for name in ("open_door_impl", "walk_impl", "look_around_impl", "listen_impl", "walk_to_impl"):
            self.assertIn(f"def {name}", source)
        self.assertGreater(sum(path.stat().st_size for path in (ROOT / "vendor" / "nowhere").rglob("*") if path.is_file()), 9_000_000)

    def test_noncommercial_attribution_is_visible(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("yuyixuanfu/nowhere", readme)
        self.assertIn("CC BY-NC 4.0", readme)
        self.assertTrue((ROOT / "LICENSE").is_file())

    def test_travel_tool_returns_context_visible_string(self):
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("NOWHERE_TRAVEL_RESULT", source)
        self.assertIn("yield _tool_context_result(action, result)", source)
        self.assertIn('"冰岛 雷克雅未克": "Reykjavik"', source)
        self.assertNotIn("yield event.plain_result(_text(result))", source)
        self.assertIn("乌有乡工具执行失败", source)


if __name__ == "__main__":
    unittest.main()
