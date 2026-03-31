from bs4 import BeautifulSoup
from email.header import decode_header
import base64

class GeocachingEmail:

    def __init__(self, raw_msg):
        self.id = raw_msg["id"]
        self.raw_msg = raw_msg

        self.sender = ""
        self.subject = ""
        self.body = ""

        self.geocacher_name = None
        self.profile_link = None
        self.message_text = None

        self._parse_email()
        self._extract_geocaching_info()

    def _decode_mime(self, value):
        if not value:
            return ""
        decoded, charset = decode_header(value)[0]
        if isinstance(decoded, bytes):
            return decoded.decode(charset or "utf-8", errors="ignore")
        return decoded

    def _get_body(self, payload):
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] in ["text/plain", "text/html"]:
                    data = part["body"].get("data")
                    if data:
                        return base64.urlsafe_b64decode(data).decode(errors="ignore")
        else:
            data = payload["body"].get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode(errors="ignore")
        return ""

    def _parse_email(self):
        headers = self.raw_msg["payload"].get("headers", [])
        for h in headers:
            if h["name"] == "From":
                self.sender = self._decode_mime(h["value"])
            elif h["name"] == "Subject":
                self.subject = self._decode_mime(h["value"])
        self.body = self._get_body(self.raw_msg["payload"])

    def _extract_geocaching_info(self):
        soup = BeautifulSoup(self.body, "html.parser")

        for a in soup.find_all("a"):
            href = a.get("href", "")
            if "geocaching.com/profile" in href:
                self.profile_link = href
                self.geocacher_name = a.text.replace("View", "").replace("’s profile", "").strip()
                break

        for p in soup.find_all("p"):
            txt = p.get_text("\n").strip()
            if txt and len(txt) > 20:
                self.message_text = txt.strip('"')
                break

    def print(self):
        print("----- EMAIL -----")
        print(f"From: {self.sender}")
        print(f"Subject: {self.subject}")
        if self.geocacher_name:
            print(f"Geocacher: {self.geocacher_name}")
        if self.profile_link:
            print(f"Profile: {self.profile_link}")
        if self.message_text:
            print("\nMessage:")
            print(self.message_text)
        else:
            print("\nBody:")
            print(self.body[:500])
        print("-----------------\n")