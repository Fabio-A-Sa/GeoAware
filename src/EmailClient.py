import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from .GeocachingEmail import GeocachingEmail
from email.header import decode_header

class EmailClient:

    SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

    def __init__(self, config, credentials, token):
        self.config = config
        self.credentials_data = credentials
        self.token_data = token
        self.service = None

    def authenticate(self):
        creds = None

        # Load credentials from dict
        flow = InstalledAppFlow.from_client_config(
            self.credentials_data,
            scopes=self.SCOPES
        )
        creds = flow.run_local_server(port=0)

        self.service = build("gmail", "v1", credentials=creds)

    def get_inbox_emails(self, max_results=10):
        results = self.service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            full_msg = self.service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full"
            ).execute()

            emails.append(GeocachingEmail(full_msg))

        return emails