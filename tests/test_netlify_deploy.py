"""Disk-gated parity test: the Netlify static deploy (web/ landing page) must
mirror the existing Vercel publish exactly, and must never claim to ship the
AI. The AI is a local desktop app; no deployment file in this tree may imply
it goes online."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_netlify_publishes_exact_web_folder():
    toml = (ROOT / "netlify.toml").read_text(encoding="utf-8")
    assert 'publish = "web"' in toml
    assert 'command = ""' in toml


def test_netlify_headers_mirror_vercel_sw_no_cache():
    headers = (ROOT / "web" / "_headers").read_text(encoding="utf-8")
    assert "/sw.js" in headers
    assert "no-cache, no-store, must-revalidate" in headers
    vercel = load_json("web/vercel.json")
    for h in vercel["headers"]:
        if h["source"] == "/sw.js":
            value = h["headers"][0]["value"]
    assert value == "no-cache, no-store, must-revalidate"


def test_all_deploy_configs_agree_on_clean_urls():
    web_vercel = load_json("web/vercel.json")
    root_vercel = load_json("vercel.json")
    assert web_vercel.get("cleanUrls") is True
    assert root_vercel.get("cleanUrls") is True
    netlify = (ROOT / "netlify.toml").read_text(encoding="utf-8")
    assert "cleanUrls" in netlify


def test_netlify_config_discloses_ai_stays_local():
    toml = (ROOT / "netlify.toml").read_text(encoding="utf-8")
    assert "local desktop application" in toml
    assert "never" in toml.lower()


def test_static_landing_deployable_unit_exists():
    assert (ROOT / "web" / "index.html").is_file()
    assert (ROOT / "web" / "app.js").is_file()
    assert (ROOT / "web" / "sw.js").is_file()
