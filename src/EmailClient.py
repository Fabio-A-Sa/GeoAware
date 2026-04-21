import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from .GeocachingEmail import GeocachingEmail
from email.message import EmailMessage

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

            emails.append(GeocachingEmail(full_msg, self.config))

        return emails
    
    def get_or_create_label(self, label_name):
        labels = self.service.users().labels().list(userId="me").execute().get("labels", [])

        for label in labels:
            if label["name"].lower() == label_name.lower():
                return label["id"]

        new_label = self.service.users().labels().create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
                "type": "user"
            }
        ).execute()

        return new_label["id"]

    def organize(self, emails, remove_from_inbox=False):
        for email in emails:
            if not email.type or email.type.lower() == "unknown":
                continue  # Skip unknown types

            # Get or create label for this email type
            label_id = self.get_or_create_label(email.type)

            # Prepare label modification body
            body = {"addLabelIds": [label_id]}
            if remove_from_inbox:
                body["removeLabelIds"] = ["INBOX"]

            # Apply label changes
            self.service.users().messages().modify(
                userId="me",
                id=email.id,
                body=body
            ).execute()

    def move(self, emails, target_label_name, remove_from_inbox=True):

        if not emails:
            return

        # Get or create the target label
        target_label_id = self.get_or_create_label(target_label_name)

        for email in emails:
            labels_to_add = [target_label_id]
            labels_to_remove = ["INBOX"] if remove_from_inbox else []

            self.service.users().messages().modify(
                userId="me",
                id=email.id,
                body={
                    "addLabelIds": labels_to_add,
                    "removeLabelIds": labels_to_remove
                }
            ).execute()

    def get_emails_from_label(self, label_name, max_results=10):

        # Find the label config
        label_config = next((l for l in self.config["labels"] if l["Name"] == label_name), None)
        if not label_config:
            raise ValueError(f"Label '{label_name}' not found in config")

        label_id = self.get_or_create_label(label_name)

        # Fetch messages from this label
        results = self.service.users().messages().list(
            userId="me",
            labelIds=[label_id],
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

            emails.append(GeocachingEmail(full_msg, self.config))

        return emails
    
    def reorganize_by_condition(self, source_labels, target_label_name, condition_func, max_results=20):
        source_label_ids = []
        for name in source_labels:
            source_label_ids.append(self.get_or_create_label(name))
        
        target_label_id = self.get_or_create_label(target_label_name)

        query = " OR ".join([f'label:"{name}"' for name in source_labels])
        
        results = self.service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        
        for msg in messages:
            full_msg = self.service.users().messages().get(
                userId="me", id=msg["id"], format="full"
            ).execute()
            
            email_obj = GeocachingEmail(full_msg, self.config)

            if condition_func(email_obj):
                current_labels = full_msg.get("labelIds", [])
                labels_to_remove = [lid for lid in source_label_ids if lid in current_labels]

                self.service.users().messages().modify(
                    userId="me",
                    id=email_obj.id,
                    body={
                        "addLabelIds": [target_label_id],
                        "removeLabelIds": labels_to_remove
                    }
                ).execute()
                print(f"Email {email_obj.id} movido para {target_label_name}")

    def _create_reply_message(self, email_obj):

        if email_obj.type == "Message Center":
            return f"""Olá {email_obj.geocacher_name},
                
Obrigado pela visita à cache {email_obj.earthcache}!
\nEspero que tenhas gostado da experiência e aprendido algo novo sobre geologia.

Cumprimentos,
\nFábio             
        """
        
        else:
            return f"""Olá {email_obj.geocacher_name},
                
Obrigado pela mensagem! Este é um email de teste enviado pelo bot GeoAware.

Cumprimentos,
Fábio             
            """

    def reply(self, emails, send=False):
        """
        Sends a reply or creates a draft for a list of GeocachingEmail objects.
        """
        if not isinstance(emails, list):
            emails = [emails]

        for email_obj in emails:
            try:

                message = self._create_reply_message(email_obj)

                # 1. Create the email message container (MIME)
                mime_msg = EmailMessage()
                mime_msg.set_content(message)

                # 2. Set Recipient (The sender of the original email)
                mime_msg['To'] = email_obj.sender_email
                
                # 3. Handle Subject (Ensure it starts with Re:)
                subject = email_obj.subject
                if not subject or not subject.lower().startswith("re:"):
                    subject = f"Re: {subject or 'Geocaching Message'}"
                mime_msg['Subject'] = subject

                # 4. Threading Headers (In-Reply-To and References)
                orig_headers = email_obj.raw_msg.get('payload', {}).get('headers', [])
                msg_id = next((h['value'] for h in orig_headers if h['name'].lower() == 'message-id'), None)

                if msg_id:
                    mime_msg['In-Reply-To'] = msg_id
                    mime_msg['References'] = msg_id

                # 5. Get ThreadId to keep the conversation grouped in Gmail
                thread_id = email_obj.raw_msg.get('threadId')

                # 6. Encode the message to base64
                encoded_message = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
                
                if send:
                    # --- SEND EMAIL ---
                    self.service.users().messages().send(
                        userId="me", 
                        body={
                            'raw': encoded_message, 
                            'threadId': thread_id
                        }
                    ).execute()
                    print(f"✅ Reply sent to {email_obj.sender_email}")
                else:
                    # --- CREATE DRAFT ---
                    # Drafts require the 'raw' data inside a 'message' key
                    self.service.users().drafts().create(
                        userId="me",
                        body={
                            'message': {
                                'raw': encoded_message,
                                'threadId': thread_id
                            }
                        }
                    ).execute()
                    print(f"📝 Draft created for {email_obj.sender_email} (Thread: {thread_id})")

            except Exception as e:
                print(f"❌ Error processing email {email_obj.id}: {e}")