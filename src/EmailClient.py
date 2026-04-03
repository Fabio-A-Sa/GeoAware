import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from .GeocachingEmail import GeocachingEmail

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
    
    def get_or_create_label(self, label_name, label_color=None):
        # List existing labels
        labels = self.service.users().labels().list(userId="me").execute().get("labels", [])

        # Check if label already exists
        for label in labels:
            if label["name"].lower() == label_name.lower():
                label_id = label["id"]
                # Update color if provided
                if label_color:
                    # Fetch full label object
                    full_label = self.service.users().labels().get(userId="me", id=label_id).execute()
                    # Update color in full label body
                    full_label["color"] = {
                        "textColor": label_color.get("textColor", "#000000"),
                        "backgroundColor": label_color.get("backgroundColor", "#FFFFFF")
                    }
                    # Send full label object to update
                    self.service.users().labels().update(
                        userId="me",
                        id=label_id,
                        body=full_label
                    ).execute()
                return label_id

        # Create new label
        label_body = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
            "type": "user"
        }

        new_label = self.service.users().labels().create(
            userId="me",
            body=label_body
        ).execute()

        # Update color if provided
        if label_color:
            full_label = self.service.users().labels().get(userId="me", id=new_label["id"]).execute()
            full_label["color"] = {
                "textColor": label_color.get("textColor", "#000000"),
                "backgroundColor": label_color.get("backgroundColor", "#FFFFFF")
            }
            self.service.users().labels().update(
                userId="me",
                id=new_label["id"],
                body=full_label
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

        # Get or create Gmail label
        # TODO: fix bug in label colors label_config.get("Color")
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