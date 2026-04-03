import json
from src.EmailClient import EmailClient

# Global file paths
CONFIG_PATH = "config.json"
CREDENTIALS_PATH = "secrets/credentials.json"
TOKEN_PATH = "secrets/token.json"

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():

    # Load all files
    config_data = load_json(CONFIG_PATH)
    credentials_data = load_json(CREDENTIALS_PATH)
    token_data = load_json(TOKEN_PATH)

    # Initialize EmailClient with loaded data
    client = EmailClient(
        config=config_data,
        credentials=credentials_data,
        token=token_data
    )

    # Authentication
    client.authenticate()

    # Organize email inbox
    # emails = client.get_inbox_emails(10)
    # client.organize(emails, remove_from_inbox=True)

    # Extract earthcaches
    # client.reorganize_by_condition(
    #    source_labels=["Message Center", "Email"],
    #    target_label_name="Earthcaches",
    #    condition_func=lambda e: e.isFromEarthcache(),
    #    max_results=100
    #)

    # emails = client.get_emails_from_label("Email", max_results=1)
    # for email in emails:
    #     print(email.message_text, end="\n\n")

    emails = client.get_emails_from_label("Earthcaches", max_results=1)
    client.reply(emails, send=False)

if __name__ == "__main__":
    main()