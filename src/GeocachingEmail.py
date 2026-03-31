from bs4 import BeautifulSoup
from email.header import decode_header
import base64
import re

class GeocachingEmail:

    def __init__(self, raw_msg, config):
        self.id = raw_msg["id"]
        self.raw_msg = raw_msg
        self.config = config

        self.sender_name = ""
        self.sender_email = ""
        self.subject = ""
        self.body = ""
        self.type = None
        self.earthcache = None

        self.geocacher_name = None
        self.profile_link = None
        self.message_text = None

        self._parse_email()
        self._extract_geocaching_info()
        self._extract_type()

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
                decoded = self._decode_mime(h["value"])
                # Split into name and email
                match = re.match(r'(.*)<(.+@.+)>', decoded)
                if match:
                    self.sender_name = match.group(1).strip().strip('"')
                    self.sender_email = match.group(2).strip()
                else:
                    self.sender_name = decoded
                    self.sender_email = ""
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

    def _extract_type(self):

        subject_lower = self.subject.lower()
        sender_lower = self.sender_name.lower()

        for label in self.config.get("labels", []):
            label_sender = label.get("Sender", "").lower()
            label_name = label.get("Name")
            label_filter = label.get("Filter", "")

            # Skip if sender does not match
            if label_sender not in sender_lower:
                continue

            # Convert filter into regex
            regex_pattern = re.escape(label_filter)
            regex_pattern = regex_pattern.replace(r"\{random\}", r".+")
            regex_pattern = regex_pattern.replace(r"\{geocacher\}", r".+")
            regex_pattern = regex_pattern.lower()

            # Check if subject matches filter pattern
            if re.search(regex_pattern, subject_lower):
                self.type = label_name
                return

        # Fallback if no match found
        self.type = "Unknown"

    def isFromEarthcache(self):
        if self.type != "Message Center":
            return False

        earthcaches = self.config.get("earthcaches", [])
        if not self.message_text:
            return False

        for code in earthcaches:
            if code in self.message_text:
                self.earthcache = code
                return True

        return False
    
    def print(self):
        print("----- EMAIL -----")
        print(f"From: {self.sender_name} <{self.sender_email}>")
        print(f"Subject: {self.subject}")
        print(f"Type: {self.type}")
        if self.geocacher_name:
            print(f"Geocacher: {self.geocacher_name}")
        print("-----------------\n")