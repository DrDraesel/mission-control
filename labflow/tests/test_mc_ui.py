"""Mission Control UI checks — the four static pages over FastAPI TestClient.

The pages are plain HTML + CSS + JS (no build step, no external hosts). This
test proves the shell exists, the binding footer is on every page, the
structural markers the JS fills are present, and that every asset is served
from this app.

The real app is preferred. A minimal static harness built from
``labflow/static`` is used only when the ``labflow.mc`` package or the ``/mc``
routes are absent (for example on a branch that has not picked up the API
work yet), so the page contract stays testable either way.
"""

from __future__ import annotations

import html as html_lib
import pathlib
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

STATIC_DIR = ROOT / "labflow" / "static"
DISCLAIMER = (
    "Lab record for research and operations. Not a certified EHR; "
    "not a medical device; clinical decisions are physician-led."
)
PAGE_URLS = {
    "overview": "/mc",
    "patient": None,  # needs an existing patient id; filled in setUp
    "integrations": "/mc/integrations",
    "inbody": "/mc/inbody",
}


def _static_harness() -> FastAPI:
    """Serve the four pages exactly as the app will, without the API package."""
    app = FastAPI(title="MC static harness")
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/mc")
    def mc_index():
        return FileResponse(str(STATIC_DIR / "mc" / "index.html"))

    @app.get("/mc/patient/{pid}")
    def mc_patient(pid: str):  # noqa: ARG001 - route shape mirrors the real app
        return FileResponse(str(STATIC_DIR / "mc" / "patient.html"))

    @app.get("/mc/integrations")
    def mc_integrations():
        return FileResponse(str(STATIC_DIR / "mc" / "integrations.html"))

    @app.get("/mc/inbody")
    def mc_inbody():
        return FileResponse(str(STATIC_DIR / "mc" / "inbody.html"))

    return app


class _AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "link":
            if values.get("rel") != "stylesheet":
                return
            value = values.get("href")
            if isinstance(value, str) and value:
                self.urls.append(("link", value))
            return
        if tag in ("script", "img"):
            value = values.get("src")
            if isinstance(value, str) and value:
                self.urls.append((tag, value))


class MissionControlUiTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.client, self.mode = self._client()
        self.patient_id = "demo-patient"
        if self.mode == "app":
            created = self.client.post("/api/patients", json={"name": "UI Test Patient"})
            self.assertEqual(created.status_code, 200, created.text)
            self.patient_id = created.json()["patient"]["id"]
        self.pages = dict(PAGE_URLS)
        self.pages["patient"] = f"/mc/patient/{self.patient_id}"

    def _client(self):
        """Prefer the real app; fall back to the static harness only if absent."""
        try:
            from labflow.app import create_app
            from labflow.patients import PatientStore
        except ImportError:
            # No API package on this branch yet; the static contract is still testable.
            return TestClient(_static_harness()), "harness"

        app = create_app(
            config={},
            store=PatientStore(pathlib.Path(self._tmp.name)),
        )
        paths = {getattr(route, "path", "") for route in app.routes}
        if "/mc" in paths:
            return TestClient(app), "app"
        return TestClient(_static_harness()), "harness"

    def get(self, url: str):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, f"{url} -> {response.status_code}")
        return response

    # -- rendering -----------------------------------------------------
    def test_every_page_returns_200(self):
        for name, url in self.pages.items():
            with self.subTest(page=name, mode=self.mode):
                self.get(url)

    def test_disclaimer_exact_on_every_page(self):
        for name, url in self.pages.items():
            with self.subTest(page=name):
                body = re.sub(r"\s+", " ", html_lib.unescape(self.get(url).text))
                self.assertIn(DISCLAIMER, body)

    def test_overview_has_patient_table_and_primary_action(self):
        html = self.get("/mc").text
        self.assertIn('id="patients-table"', html)
        self.assertIn("New patient / intake", html)
        self.assertIn("Sync all", html)
        self.assertIn("Unlinked sessions", html)
        self.assertIn('id="health-strip"', html)
        self.assertIn("No patients in the record yet", html)

    def test_chart_has_all_source_cards_and_export(self):
        html = self.get(self.pages["patient"]).text
        for source in ("bertec", "runtrack", "neurosync", "inbody", "intake"):
            with self.subTest(source=source):
                self.assertIn(f'data-source-card="{source}"', html)
        self.assertIn("Export chart HTML", html)
        self.assertIn('id="timeline"', html)
        self.assertIn("No sessions recorded for this patient yet", html)
        self.assertIn("No Bertec data yet.", html)

    def test_integrations_columns(self):
        html = self.get("/mc/integrations").text
        for header in ("Source", "Path / endpoint", "Reachable", "Sessions found",
                       "Last checked", "What to do"):
            with self.subTest(header=header):
                self.assertIn(header, html)
        self.assertIn("bertec-jump", html)

    def test_inbody_manual_warning_and_csv_template(self):
        html = html_lib.unescape(self.get("/mc/inbody").text)
        self.assertIn("manual entry — verify against the device printout", html.lower())
        self.assertIn("inbody-template.csv", html)
        for field in ("weight_kg", "skeletal_muscle_kg", "body_fat_kg", "body_fat_pct",
                      "visceral_fat", "lean_mass_kg", "bmi"):
            with self.subTest(field=field):
                self.assertIn(f'id="{field}"', html)

    # -- assets --------------------------------------------------------
    def test_no_external_script_or_style_host(self):
        for name, url in self.pages.items():
            parser = _AssetParser()
            parser.feed(self.get(url).text)
            for kind, asset in parser.urls:
                with self.subTest(page=name, kind=kind, asset=asset):
                    self.assertFalse(
                        re.match(r"(?:https?:)?//", asset),
                        f"{name} loads an external asset: {asset}",
                    )
                    self.assertTrue(
                        asset.startswith("/static/"),
                        f"{name} asset is not served by this app: {asset}",
                    )

    def test_static_css_js_and_template_are_served(self):
        for path in (
            "/static/mc/mc.css",
            "/static/mc/mc.js",
            "/static/mc/lab-ui/tokens.css",
            "/static/mc/lab-ui/components.css",
            "/static/mc/inbody-template.csv",
        ):
            with self.subTest(path=path):
                response = self.get(path)
                self.assertGreaterEqual(len(response.content), 50)

    def test_js_targets_the_documented_api(self):
        script = (STATIC_DIR / "mc" / "mc.js").read_text(encoding="utf-8")
        for endpoint in ("/overview", "/patients", "/integrations", "/inbody", "/export.html"):
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, script)

    def test_csv_template_header_matches_spec(self):
        csv_text = (STATIC_DIR / "mc" / "inbody-template.csv").read_text(encoding="utf-8").strip()
        self.assertEqual(
            csv_text,
            "measured_at,weight_kg,skeletal_muscle_kg,body_fat_kg,body_fat_pct,"
            "visceral_fat,lean_mass_kg,bmi",
        )


if __name__ == "__main__":
    unittest.main()
