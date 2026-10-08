"""
Tests del modo demo (StickerControl Demo Roura).

Correr desde backend/:
    .venv/Scripts/python -m unittest discover -s tests -v      (Windows)
    .venv/bin/python -m unittest discover -s tests -v          (Linux)

Usan una base SQLite temporal propia: nunca tocan stickercontrol.db.
"""

import os
import secrets
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta

_TMP_DIR = tempfile.mkdtemp(prefix="sc_demo_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TMP_DIR, 'demo_test.db')}"
os.environ["DEMO_MODE"] = "true"
os.environ["SESSION_SECRET"] = secrets.token_hex(32)
os.environ["SESSION_COOKIE_SECURE"] = "false"
os.environ["DEMO_LOGIN_RATE_LIMIT"] = "1000"
os.environ["DEMO_MAX_SANDBOXES"] = "300"

from fastapi.testclient import TestClient  # noqa: E402

from app import demo, models  # noqa: E402
from app.database import SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from seed_db import DEFAULT_CSV_PATH, seed as seed_catalog  # noqa: E402


def _codes_by_status(db, user_id):
    """Faltantes y repetidas calculadas en el test, a partir de las filas
    crudas y las reglas documentadas en status.py (independiente de crud.py)."""
    stickers = db.query(models.MasterSticker).all()
    entries = {
        e.sticker_id: e for e in db.query(models.UserSticker).filter(models.UserSticker.user_id == user_id)
    }
    missing, duplicates = set(), set()
    for s in stickers:
        e = entries.get(s.id)
        qty = e.quantity if e else 0
        pasted = e.is_pasted if e else False
        if not pasted and qty == 0:
            missing.add(s.code)
        if (pasted and qty >= 1) or (not pasted and qty >= 2):
            duplicates.add(s.code)
    return missing, duplicates


def setUpModule():
    init_db()
    seed_catalog(DEFAULT_CSV_PATH)
    db = SessionLocal()
    demo.seed_collectors(db)
    db.close()


def tearDownModule():
    engine.dispose()
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


class DemoTestCase(unittest.TestCase):
    def setUp(self):
        os.environ["DEMO_MODE"] = "true"
        demo.login_limiter.reset()

    def new_visitor(self):
        client = TestClient(app)
        res = client.post("/api/auth/demo")
        self.assertEqual(res.status_code, 200, res.text)
        return client, res.json()


class TestAccess(DemoTestCase):
    def test_google_login_disabled_in_demo(self):
        res = TestClient(app).post("/api/auth/google", json={"credential": "x"})
        self.assertEqual(res.status_code, 404)

    def test_demo_login_without_registration(self):
        client, user = self.new_visitor()
        self.assertEqual(user["name"], demo.VISITOR_NAME)
        self.assertTrue(user["email"].endswith(demo.VISITOR_DOMAIN))
        self.assertEqual(client.get("/api/auth/me").json()["id"], user["id"])

    def test_requests_without_session_are_rejected(self):
        self.assertEqual(TestClient(app).get("/api/reports/album").status_code, 401)

    def test_docs_hidden_in_demo(self):
        self.assertEqual(TestClient(app).get("/docs").status_code, 404)
        self.assertEqual(TestClient(app).get("/openapi.json").status_code, 404)

    def test_demo_endpoint_absent_when_demo_mode_off(self):
        os.environ["DEMO_MODE"] = "false"
        self.assertEqual(TestClient(app).post("/api/auth/demo").status_code, 404)


class TestPreloadedAlbum(DemoTestCase):
    def test_album_partially_completed_with_missing_and_duplicates(self):
        client, _ = self.new_visitor()
        album = client.get("/api/reports/album").json()
        countries = [c for g in album["groups"] for c in g["countries"]] + album["special"]
        total = sum(c["summary"]["total"] for c in countries)
        pegadas = sum(c["summary"]["pegadas"] for c in countries)
        self.assertEqual(total, 980)
        self.assertTrue(0.4 * total < pegadas < 0.7 * total, pegadas)

        missing = client.get("/api/reports/missing").json()
        duplicates = client.get("/api/reports/duplicates").json()
        self.assertGreater(sum(len(c["numbers"]) for c in missing["by_country"]), 300)
        self.assertGreater(len(duplicates["by_country"]), 10)

    def test_state_breakdown_is_consistent(self):
        """980 = pegadas + faltantes + disponibles para pegar (conseguidas sin
        pegar). Las repetidas son copias extra, no figuritas distintas."""
        client, user = self.new_visitor()
        album = client.get("/api/reports/album").json()
        countries = [c for g in album["groups"] for c in g["countries"]] + album["special"]
        stickers = [s for c in countries for s in c["stickers"]]
        by_status = {}
        for s in stickers:
            by_status[s["status"]] = by_status.get(s["status"], 0) + 1

        pegadas = by_status["PEGADA_SIN_REPETIDA"] + by_status["PEGADA_CON_REPETIDA"]
        self.assertEqual(len(stickers), 980)
        self.assertEqual(
            (pegadas, by_status["FALTANTE"], by_status["DISPONIBLE_PARA_PEGAR"]), (539, 429, 12)
        )
        self.assertEqual(pegadas + by_status["FALTANTE"] + by_status["DISPONIBLE_PARA_PEGAR"], 980)
        self.assertEqual(sum(s["repetidas"] for s in stickers), 168)
        self.assertEqual(sum(1 for s in stickers if s["repetidas"] > 0), 98)
        for s in stickers:
            if s["status"] == "FALTANTE":
                self.assertEqual((s["quantity"], s["is_pasted"], s["repetidas"]), (0, False, 0))
            if s["status"] == "DISPONIBLE_PARA_PEGAR":
                self.assertEqual(s["repetidas"], max(s["quantity"] - 1, 0))

    def test_every_visitor_gets_the_same_starting_album(self):
        a, _ = self.new_visitor()
        b, _ = self.new_visitor()
        self.assertEqual(a.get("/api/reports/missing").json(), b.get("/api/reports/missing").json())


class TestIsolation(DemoTestCase):
    def test_changes_do_not_leak_between_visitors(self):
        a, _ = self.new_visitor()
        b, _ = self.new_visitor()
        missing_code = a.get("/api/reports/missing").json()["by_country"][0]
        sticker = a.get(
            "/api/stickers/search", params={"country_code": missing_code["country_code"], "limit": 500}
        ).json()["items"]
        target = next(s for s in sticker if s["number"] == missing_code["numbers"][0])

        res = a.post(f"/api/collection/{target['id']}/paste")
        self.assertTrue(res.json()["is_pasted"])

        b_view = b.get("/api/stickers/search", params={"q": target["code"]}).json()["items"]
        self.assertFalse(next(s for s in b_view if s["id"] == target["id"])["is_pasted"])

    def test_mark_and_unmark(self):
        client, _ = self.new_visitor()
        sticker = client.get("/api/stickers/search", params={"limit": 1}).json()["items"][0]
        self.assertTrue(client.post(f"/api/collection/{sticker['id']}/paste").json()["is_pasted"])
        self.assertFalse(client.post(f"/api/collection/{sticker['id']}/unpaste").json()["is_pasted"])

    def test_visitors_never_appear_as_collectors(self):
        a, user_a = self.new_visitor()
        b, _ = self.new_visitor()
        ids = {u["user_id"] for u in b.get("/api/nearby").json()["users"]}
        self.assertNotIn(user_a["id"], ids)
        self.assertEqual(len(ids), len(demo.COLLECTORS))
        self.assertEqual(b.get(f"/api/trades/with-user/{user_a['id']}").status_code, 404)
        self.assertEqual(b.get(f"/api/nearby/{user_a['id']}/contact-message").status_code, 404)

    def test_profile_is_read_only(self):
        client, _ = self.new_visitor()
        res = client.patch("/api/profile", json={"is_public": True, "contact_whatsapp": "5491100000000"})
        self.assertEqual(res.status_code, 403)
        self.assertFalse(client.get("/api/profile").json()["is_public"])


class TestMatchesComeFromData(DemoTestCase):
    def test_nearby_matches_equal_set_intersections_of_fictitious_data(self):
        client, user = self.new_visitor()
        nearby = client.get("/api/nearby").json()["users"]
        self.assertTrue(any(u["match_count"] > 0 for u in nearby))

        db = SessionLocal()
        try:
            my_missing, my_dups = _codes_by_status(db, user["id"])
            for other in nearby:
                their_missing, their_dups = _codes_by_status(db, other["user_id"])
                self.assertEqual(set(other["stickers_i_need_that_user_has"]), my_missing & their_dups)
                self.assertEqual(set(other["stickers_user_needs_that_i_have"]), their_missing & my_dups)
        finally:
            db.close()

    def test_matches_react_to_visitor_changes(self):
        client, _ = self.new_visitor()
        collector = max(client.get("/api/nearby").json()["users"], key=lambda u: u["match_count"])
        code = collector["stickers_i_need_that_user_has"][0]
        sticker = client.get("/api/stickers/search", params={"q": code}).json()["items"]
        sticker = next(s for s in sticker if s["code"] == code)

        client.post(f"/api/collection/{sticker['id']}/paste")
        trade = client.get(f"/api/trades/with-user/{collector['user_id']}").json()
        self.assertNotIn(code, trade["i_can_receive"])

    def test_no_real_whatsapp_or_email_links(self):
        client, _ = self.new_visitor()
        for other in client.get("/api/nearby").json()["users"]:
            self.assertFalse(other["has_whatsapp"])
            self.assertFalse(other["has_email"])
            msg = client.get(f"/api/nearby/{other['user_id']}/contact-message").json()
            self.assertIsNone(msg["whatsapp_url"])
            self.assertIsNone(msg["mailto_url"])
            self.assertIn("StickerControl 2026", msg["text"])
            trade = client.get(f"/api/trades/with-user/{other['user_id']}").json()
            self.assertIsNone(trade["whatsapp_url"])
            self.assertIsNone(trade["mailto_url"])


class TestAbuseLimits(DemoTestCase):
    def test_quantity_cap(self):
        os.environ["DEMO_MAX_QUANTITY"] = "3"
        try:
            client, _ = self.new_visitor()
            sticker = client.get("/api/stickers/search", params={"limit": 1}).json()["items"][0]
            client.post(f"/api/collection/{sticker['id']}/mark-missing")
            for _ in range(3):
                self.assertEqual(client.post(f"/api/collection/{sticker['id']}/increment").status_code, 200)
            self.assertEqual(client.post(f"/api/collection/{sticker['id']}/increment").status_code, 400)
        finally:
            del os.environ["DEMO_MAX_QUANTITY"]

    def test_notes_length_cap(self):
        client, _ = self.new_visitor()
        sticker = client.get("/api/stickers/search", params={"limit": 1}).json()["items"][0]
        ok = client.patch(f"/api/collection/{sticker['id']}/notes", json={"notes": "x" * 280})
        too_long = client.patch(f"/api/collection/{sticker['id']}/notes", json={"notes": "x" * 281})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(too_long.status_code, 400)

    def test_login_rate_limit_per_ip(self):
        os.environ["DEMO_LOGIN_RATE_LIMIT"] = "3"
        try:
            client = TestClient(app)
            codes = [client.post("/api/auth/demo").status_code for _ in range(4)]
            self.assertEqual(codes, [200, 200, 200, 429])
        finally:
            os.environ["DEMO_LOGIN_RATE_LIMIT"] = "1000"

    def test_restart_replaces_sandbox_instead_of_accumulating(self):
        client, first = self.new_visitor()
        second = client.post("/api/auth/demo").json()
        # SQLite puede reutilizar el id; lo que identifica al sandbox es el email.
        self.assertNotEqual(first["email"], second["email"])
        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(models.User).filter(models.User.email == first["email"]).count(), 0
            )
        finally:
            db.close()

    def test_sandbox_cap_evicts_oldest(self):
        db = SessionLocal()
        demo.delete_all_visitors(db)
        db.close()
        os.environ["DEMO_MAX_SANDBOXES"] = "3"
        try:
            clients = [self.new_visitor() for _ in range(4)]
            db = SessionLocal()
            try:
                count = db.query(models.User).filter(models.User.email.like(f"%{demo.VISITOR_DOMAIN}")).count()
            finally:
                db.close()
            self.assertEqual(count, 3)
            self.assertEqual(clients[0][0].get("/api/auth/me").status_code, 401)
            self.assertEqual(clients[3][0].get("/api/auth/me").status_code, 200)
        finally:
            os.environ["DEMO_MAX_SANDBOXES"] = "300"


class TestReset(DemoTestCase):
    def test_purge_expired_sandbox_and_its_share_link(self):
        client, user = self.new_visitor()
        token = client.post("/api/share/generate").json()["token"]
        self.assertEqual(TestClient(app).get(f"/api/public/{token}/album").status_code, 200)

        db = SessionLocal()
        try:
            deleted = demo.purge_expired_visitors(db, now=datetime.utcnow() + timedelta(hours=7))
            self.assertGreaterEqual(deleted, 1)
            self.assertEqual(db.query(models.User).filter(models.User.email == user["email"]).count(), 0)
        finally:
            db.close()

        self.assertEqual(client.get("/api/reports/album").status_code, 401)
        self.assertEqual(TestClient(app).get(f"/api/public/{token}/album").status_code, 404)

    def test_stale_cookie_never_opens_another_visitors_sandbox(self):
        old_client, old_user = self.new_visitor()
        db = SessionLocal()
        demo.delete_all_visitors(db)
        db.close()
        _, new_user = self.new_visitor()
        # Aunque SQLite reutilice el id, la cookie vieja no da acceso.
        self.assertEqual(old_client.get("/api/auth/me").status_code, 401)
        self.assertIsNotNone(new_user["id"])

    def test_logout_deletes_sandbox(self):
        client, user = self.new_visitor()
        client.post("/api/auth/logout")
        db = SessionLocal()
        try:
            self.assertEqual(db.query(models.User).filter(models.User.email == user["email"]).count(), 0)
        finally:
            db.close()

    def test_reset_keeps_collectors_and_removes_visitors(self):
        self.new_visitor()
        db = SessionLocal()
        try:
            demo.delete_all_visitors(db)
            demo.seed_collectors(db)
            visitors = db.query(models.User).filter(models.User.email.like(f"%{demo.VISITOR_DOMAIN}")).count()
            collectors = db.query(models.User).filter(models.User.email.like(f"%{demo.COLLECTOR_DOMAIN}")).count()
        finally:
            db.close()
        self.assertEqual((visitors, collectors), (0, len(demo.COLLECTORS)))

    def test_admin_refuses_non_demo_database(self):
        db = SessionLocal()
        try:
            real = models.User(email="persona@example.com", name="Real")
            db.add(real)
            db.commit()
            with self.assertRaises(RuntimeError):
                demo.assert_demo_database(db)
            db.delete(real)
            db.commit()
            demo.assert_demo_database(db)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
