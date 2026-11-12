import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = (
    "plugin.json",
    ".grok-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
)
MCP_FILES = ("mcp.json", ".mcp.json")
ENDPOINT = "https://speedbot.dev/mcp/core"
SKILL = ROOT / "skills/hire-code-review/SKILL.md"


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_package():
    assert all(load_json(path)["name"] == "speedbot" for path in MANIFESTS)
    codex = load_json(".codex-plugin/plugin.json")
    assert codex["skills"] == "./skills/"
    assert codex["mcpServers"] == "./.mcp.json"
    for path, transport in zip(MCP_FILES, ("streamable-http", "http")):
        assert load_json(path)["mcpServers"] == {
            "speedbot": {"type": transport, "url": ENDPOINT}
        }, f"{path} must use the existing public MCP connection"

    harness = load_json("package.json")
    assert harness["dsh"]["bundle"]["patch"] == "./cordis.patch.yml"
    assert harness["files"] == ["cordis.patch.yml"]
    assert not any(field in harness for field in ("scripts", "dependencies", "bin"))
    patch_lines = (ROOT / "cordis.patch.yml").read_text(encoding="utf-8").splitlines()
    assert [line.strip() for line in patch_lines] == [
        "- insert:", "- id: mcp-speedbot", "name: '@deepseek-ai/dsh-mcp-client'",
        "config:", "serverName: speedbot", "transport: streamable-http", f"url: {ENDPOINT}",
    ]

    assert list((ROOT / "skills").glob("*/SKILL.md")) == [SKILL]
    frontmatter, body = SKILL.read_text(encoding="utf-8").split("---\n", 2)[1:]
    assert frontmatter.startswith("name: hire-code-review\ndescription: ")
    examples = re.findall(r"```json\n(.*?)\n```", body, flags=re.DOTALL)
    assert len(examples) == 1
    plan = json.loads(examples[0])
    assert set(plan) == {"operation", "need", "agents", "budget_usdc"}
    assert plan["operation"] == "plan"
    assert plan["agents"] == 1 and plan["budget_usdc"] == "0"
    assert "https://github.com/OWNER/REPO" in plan["need"]
    print("Package paths, MCP configuration and plan example passed.")


def release_version(value):
    assert re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value)
    return tuple(map(int, value.split(".")))


def check_release(base):
    version = load_json("plugin.json")["version"]
    assert all(load_json(path)["version"] == version for path in MANIFESTS)
    assert (ROOT / f"RELEASE-{version}.md").is_file()
    previous = json.loads(subprocess.check_output(
        ["git", "show", f"{base}:plugin.json"], cwd=ROOT, text=True
    ))["version"]
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", base], cwd=ROOT, text=True
    ).splitlines()
    current_version = release_version(version)
    base_version = release_version(previous)
    assert current_version >= base_version, "Plugin version cannot go backwards"
    if any(path in (*MANIFESTS, *MCP_FILES) or path.startswith("skills/") for path in changed):
        assert current_version > base_version, "Plugin changes require a higher version"
    print(f"Plugin release policy passed for {version}.")


if __name__ == "__main__":
    if sys.argv[1:] == ["test"]:
        test_package()
    elif len(sys.argv) == 3 and sys.argv[1] == "release-policy":
        check_release(sys.argv[2])
    else:
        raise SystemExit("Usage: check_plugin.py test | release-policy BASE_SHA")
