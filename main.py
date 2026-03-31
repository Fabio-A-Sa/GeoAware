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

    client.authenticate()
    emails = client.get_inbox_emails(100)
    client.organize(emails, remove_from_inbox=True)

    for email in emails:
        email.print()

if __name__ == "__main__":
    main()