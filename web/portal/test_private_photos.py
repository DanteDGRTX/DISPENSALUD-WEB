from io import BytesIO
from pathlib import Path
import tempfile
import time
import uuid
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import SimpleTestCase, override_settings
import jwt
from PIL import Image

from portal.private_photos.errors import PhotoError
from portal.private_photos.store import PhotoStore

def fixture(format="PNG", size=(80, 60)):
    buffer = BytesIO()
    Image.new("RGB", size, (25, 90, 160)).save(buffer, format)
    return buffer.getvalue()

class PrivatePhotoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.override = override_settings(PRIVATE_PHOTO_ROOT=Path(self.directory.name), FIREBASE_EMULATORS=False, FIREBASE_PROJECT_ID="dispensalud-130f5")
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.key_patch = patch("portal.private_photos.identity.public_key", return_value=self.key.public_key())
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)
        self.remote = patch("portal.private_photos.identity.remote_json", side_effect=self.upstream).start()
        self.addCleanup(patch.stopall)
        self.revoked = False
        self.offline = False

    def token(self, uid="accountA", **changes):
        now = int(time.time())
        claims = {"sub": uid, "aud": "dispensalud-130f5", "iss": "https://securetoken.google.com/dispensalud-130f5", "iat": now, "exp": now+3600, "auth_time": now, "email_verified": True, **changes}
        return jwt.encode(claims, self.key, algorithm="RS256", headers={"kid": "fixture-key"})

    def upstream(self, url, token=None, body=None):
        if self.offline:
            raise PhotoError("upstream", "Sin conexión.", 503)
        assert url.startswith(("https://identitytoolkit.googleapis.com/", "https://firestore.googleapis.com/"))
        if "accounts:lookup" in url:
            claims=jwt.decode(body["idToken"], options={"verify_signature":False})
            return {"users":[{"localId":claims["sub"], "emailVerified":True, "validSince":str(int(time.time())+100 if self.revoked else 0)}]}
        uid = token and jwt.decode(token, options={"verify_signature":False})["sub"]
        if uid != "accountA" or not url.endswith("/patients/patientA"):
            raise PhotoError("not-found", "Paciente no disponible.", 404)
        return {"fields":{"ownerUid":{"stringValue":uid},"id":{"stringValue":"patientA"},"deleted":{"booleanValue":False}}}

    def put(self, path="/api/photos/v1/profile/", uid="accountA", etag="none", data=None, mime="image/png", mutation=None):
        return self.client.put(path, fixture() if data is None else data, content_type=mime, HTTP_AUTHORIZATION="Bearer "+self.token(uid), HTTP_IF_MATCH=etag, HTTP_IDEMPOTENCY_KEY=mutation or str(uuid.uuid4()))

    def get(self, path, uid="accountA"):
        return self.client.get(path, HTTP_AUTHORIZATION="Bearer "+self.token(uid))

    def test_upload_read_normalization_private_headers(self):
        response=self.put();self.assertEqual(response.status_code,200)
        photo=response.json();self.assertRegex(photo["reference"],r"^private-photo:v1:[a-f0-9]{32}$")
        response=self.get("/api/photos/v1/files/"+photo["photoId"]+"/")
        self.assertEqual(response.status_code,200)
        data=b"".join(response.streaming_content)
        with Image.open(BytesIO(data)) as image:
            self.assertEqual(image.format,"JPEG");self.assertFalse(image.getexif());self.assertLessEqual(max(image.size),512)
        self.assertIn("no-store",response["Cache-Control"])
        self.assertEqual(response["Vary"],"Authorization")
        self.assertNotIn("http",photo["reference"])

    def test_cross_account_cannot_read_or_mutate_patient(self):
        response=self.put("/api/photos/v1/patients/patientA/");self.assertEqual(response.status_code,200)
        photo=response.json()
        self.assertEqual(self.get("/api/photos/v1/files/"+photo["photoId"]+"/","accountB").status_code,404)
        self.assertEqual(self.put("/api/photos/v1/patients/patientA/",uid="accountB").status_code,404)
        self.assertEqual(self.get("/api/photos/v1/","accountB").json(),{"photos":[]})

    def test_signature_audience_expiry_unverified_and_revocation(self):
        for token,status in [(self.token(exp=1),401),(self.token(aud="other"),401),(self.token(email_verified=False),403),(jwt.encode({"sub":"accountA"},key="",algorithm="none"),401)]:
            self.assertEqual(self.client.get("/api/photos/v1/",HTTP_AUTHORIZATION="Bearer "+token).status_code,status)
        self.revoked=True;self.assertEqual(self.get("/api/photos/v1/").status_code,401)
        self.assertEqual(self.client.get("/api/photos/v1/").status_code,401)

    def test_formats_corrupt_mismatched_large_and_dimensions(self):
        self.assertEqual(self.put(data=b"not-image").status_code,422)
        self.assertEqual(self.put(mime="image/jpeg").status_code,415)
        self.assertEqual(self.put(data=b"x"*2097153).status_code,413)
        self.assertEqual(self.put(data=fixture(size=(3000,2000))).status_code,422)
        self.assertEqual(self.put(data=b'<svg/>',mime="image/svg+xml").status_code,415)
        self.assertEqual(self.put(data=b'{"url":"http://invalid.example"}',mime="application/json").status_code,415)

    def test_replacement_delete_conflict_and_idempotent_retry(self):
        mutation=str(uuid.uuid4());first=self.put(mutation=mutation).json()
        self.assertEqual(self.put(mutation=mutation).json(),first)
        self.assertEqual(self.put().status_code,409)
        second=self.put(etag=first["etag"],data=fixture(size=(90,90))).json()
        self.assertNotEqual(first["photoId"],second["photoId"])
        self.assertEqual(self.get("/api/photos/v1/files/"+first["photoId"]+"/").status_code,404)
        response=self.client.delete("/api/photos/v1/profile/",HTTP_AUTHORIZATION="Bearer "+self.token(),HTTP_IF_MATCH=second["etag"])
        self.assertEqual(response.json()["state"],"deleted")
        self.assertEqual(len(list(Path(self.directory.name).rglob("*.jpg"))),0)

    def test_quota_and_failed_connection_do_not_report_success(self):
        with override_settings(PRIVATE_PHOTO_UID_BYTES=1):
            self.assertEqual(self.put().status_code,507)
        self.offline=True;self.assertEqual(self.put().status_code,503)
        self.assertEqual(len(list(Path(self.directory.name).rglob("*.jpg"))),0)

    def test_reopening_store_preserves_reference_and_bytes(self):
        first=self.put().json()
        store=PhotoStore();self.assertEqual(store.metadata("profile",store.row("accountA","profile")),first);store.close()
        self.assertEqual(self.get("/api/photos/v1/profile/").json(),first)

    def test_csrf_cookie_does_not_authorize_and_origin_rejected(self):
        self.assertEqual(self.client.put("/api/photos/v1/profile/",fixture(),content_type="image/png").status_code,401)
        self.assertEqual(self.client.get("/api/photos/v1/",HTTP_AUTHORIZATION="Bearer "+self.token(),HTTP_ORIGIN="https://other.example").status_code,403)
        self.assertEqual(self.client.get("/api/photos/v1/?token=fictitious",HTTP_AUTHORIZATION="Bearer "+self.token()).status_code,400)
