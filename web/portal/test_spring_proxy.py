from io import BytesIO
from unittest.mock import patch
from django.test import SimpleTestCase, override_settings
from portal.spring_proxy import NoRedirect

class Remote(BytesIO):
    code = 200
    headers = {"Content-Type": "text/html"}
    def __init__(self):
        super().__init__(b"<section>FICTICIO</section>")

@override_settings(SPRING_API_URL="http://127.0.0.1:8091")
class SpringProxyTests(SimpleTestCase):
    def test_missing_token_and_unknown_routes_do_not_reach_service(self):
        with patch("portal.spring_proxy.build_opener") as opener:
            self.assertEqual(self.client.get("/api/spring/workspace").status_code,401)
            self.assertEqual(self.client.get("/api/spring/admin").status_code,405)
            self.assertEqual(self.client.get("/api/spring/workspace?token=x").status_code,405)
            opener.assert_not_called()

    def test_proxy_forwards_token_not_cookies_and_disables_redirects(self):
        with patch("portal.spring_proxy.build_opener") as opener:
            opener.return_value.open.return_value=Remote()
            response=self.client.get("/api/spring/workspace",HTTP_AUTHORIZATION="Bearer test-token",HTTP_COOKIE="sessionid=private")
            self.assertEqual(response.status_code,200)
            request=opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url,"http://127.0.0.1:8091/workspace")
            self.assertEqual(request.get_header("Authorization"),"Bearer test-token")
            self.assertIsNone(request.get_header("Cookie"))
            self.assertIn("no-store",response["Cache-Control"])
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,"",{},"https://other.invalid"))

    def test_cross_origin_and_large_forms_are_rejected(self):
        self.assertEqual(self.client.get("/api/spring/workspace",HTTP_AUTHORIZATION="Bearer test-token",HTTP_ORIGIN="https://other.invalid").status_code,403)
        response=self.client.post("/api/spring/patients",data="x="+"z"*70000,content_type="application/x-www-form-urlencoded",HTTP_AUTHORIZATION="Bearer test-token")
        self.assertEqual(response.status_code,413)

    @override_settings(SPRING_API_URL="")
    def test_disabled_integration_is_absent_and_flagged(self):
        self.assertEqual(self.client.get("/api/spring/workspace").status_code,404)
        self.assertContains(self.client.get("/panel/"),'"springEnabled": false')
