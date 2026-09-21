"""Disk-gated tests for the EDU-AIR SMART SURFACE PWA and its static deploy.

Everything here asserts against real files on disk: the PWA shell, the service
worker wiring, and the three deploy configs (Vercel / Netlify / Render). The
whole point is that they agree, and that no deploy config claims to ship the
local desktop AI.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SW_NO_CACHE = "no-cache, no-store, must-revalidate"


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def load_json(name):
    return json.loads(read(name))


def test_app_shell_files_exist():
    for name in [
        "index.html",
        "app.js",
        "i18n.js",
        "styles.css",
        "sw.js",
        "manifest.webmanifest",
    ]:
        assert (ROOT / name).is_file(), f"missing PWA shell file: {name}"


def test_manifest_is_valid_and_honest():
    m = load_json("manifest.webmanifest")
    assert m["name"] == "EDU-AIR SMART SURFACE"
    assert m["short_name"] == "EDU-AIR"
    assert m["start_url"] == "./"
    assert m["scope"] == "./"
    assert m["display"] == "standalone"
    assert set(m["locales"]) == {"en", "fr", "ar", "nl"}

    sizes = set()
    for icon in m["icons"]:
        assert (ROOT / icon["src"]).is_file(), f"manifest references missing {icon['src']}"
        sizes.add(icon["sizes"])
    assert "192x192" in sizes and "512x512" in sizes


def test_manifest_theme_color_matches_html_meta():
    m = load_json("manifest.webmanifest")
    html = read("index.html")
    match = re.search(r'<meta\s+name="theme-color"\s+content="(#[0-9a-fA-F]{6})"', html)
    assert match, "index.html is missing a theme-color meta tag"
    assert match.group(1).lower() == m["theme_color"].lower()


def test_index_html_links_manifest_and_ios_meta():
    html = read("index.html")
    assert 'rel="manifest" href="manifest.webmanifest"' in html
    assert 'name="apple-mobile-web-app-capable"' in html
    assert 'rel="apple-touch-icon"' in html


def test_app_js_registers_the_service_worker():
    app = read("app.js")
    assert "serviceWorker" in app
    assert re.search(r'register\(\s*"\./sw\.js"', app), "sw.js is never registered"
    assert re.search(r'scope\s*:\s*"\./"', app), "service worker scope should be ./"


def test_app_js_handles_install_and_connectivity():
    app = read("app.js")
    assert "beforeinstallprompt" in app
    assert "appinstalled" in app
    assert '"online"' in app and '"offline"' in app
    assert "btnInstall" in app


def test_sw_precaches_the_shell_and_falls_back_offline():
    sw = read("sw.js")
    assert "caches.open" in sw
    assert '"./index.html"' in sw
    assert "addAll" in sw
    assert "SKIP_WAITING" in sw


def test_desktop_zip_is_never_deployed():
    assert "downloads/" in read(".vercelignore")
    assert "downloads/" in read(".gitignore")


def test_all_deploy_configs_agree_on_sw_no_cache():
    vercel = load_json("vercel.json")
    sw_headers = [h for h in vercel["headers"] if h["source"] == "/sw.js"]
    assert sw_headers and sw_headers[0]["headers"][0]["value"] == SW_NO_CACHE

    assert SW_NO_CACHE in read("netlify.toml")
    assert SW_NO_CACHE in read("_headers")
    assert SW_NO_CACHE in read("render.yaml")


def test_all_deploy_configs_publish_the_repo_root():
    assert load_json("vercel.json").get("cleanUrls") is True

    netlify = read("netlify.toml")
    assert 'publish = "."' in netlify
    assert 'command = ""' in netlify

    render = read("render.yaml")
    assert "runtime: static" in render
    assert "staticPublishPath: ." in render


def test_deploy_configs_disclose_ai_stays_local():
    for name in ["netlify.toml", "render.yaml"]:
        text = read(name).lower()
        assert "local" in text and "never" in text, f"{name} should say the AI stays local"
