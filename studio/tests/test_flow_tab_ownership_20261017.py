"""Regression: CDP ordering cannot establish which tab belongs to a job."""
import io, json, sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio_mcp import accounts, projects

class TabOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.account = accounts.active_account()
        self.url = projects.url_for(self.account)
        assert self.url
        # Chrome lists the NEW production tab first; the original is second.
        self.pages = [
            {"id": "B"*32, "type": "page", "url": self.url},
            {"id": "A"*32, "type": "page", "url": self.url},
            {"id": "C"*32, "type": "page", "url": "about:blank"},
        ]
        self.closed = []
    def cdp(self, request, **kwargs):
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if "/json/close/" in url:
            target = url.rsplit("/", 1)[-1]
            self.closed.append(target)
            self.pages = [p for p in self.pages if p["id"] != target]
            return io.BytesIO(b"true")
        if "/json/list" in url:
            return io.BytesIO(json.dumps(self.pages).encode())
        raise AssertionError("Unexpected CDP mutation: " + url)
    def test_background_cleanup_preserves_original_and_unowned_tabs(self):
        before = list(self.pages)
        with patch("studio_mcp.transport._isolated"), \
             patch.object(accounts, "connection_check", return_value={"connected": True}), \
             patch.object(accounts, "_pid_browser_for_account", return_value=123), \
             patch.object(projects, "urlopen", side_effect=self.cdp):
            projects.cleanup_duplicate_tool_tabs(self.account, self.url)
        self.assertEqual(self.closed, [], "Background cleanup closed unowned tabs")
        self.assertEqual(self.pages, before)
    def test_verify_reports_duplicates_without_closing_them(self):
        with patch("studio_mcp.transport._isolated"), \
             patch.object(accounts, "_require_idle"), \
             patch.object(accounts, "connection_check", return_value={"connected": True}), \
             patch.object(accounts, "_pid_browser_for_account", return_value=123), \
             patch.object(accounts, "flow_auth_status", return_value={"authenticated": True}), \
             patch("studio_mcp.transport.LocalFlowMcpTransport", side_effect=AssertionError("Duplicate preflight must not start MCP")), \
             patch.object(projects, "urlopen", side_effect=self.cdp):
            result = accounts.verify_mcp_connection(self.account["id"], tool_url=self.url)
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "FLOW_MCP_DUPLICATE_TOOL_TABS")
        self.assertEqual(result["tab_count"], 2)
        self.assertEqual(self.closed, [])
if __name__ == "__main__":
    unittest.main()
