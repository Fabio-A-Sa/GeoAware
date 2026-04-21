import json
import argparse
from src.EmailClient import EmailClient
from src.dashboard import run_dashboard

CONFIG_PATH = "config.json"
CREDENTIALS_PATH = "secrets/credentials.json"
TOKEN_PATH = "secrets/token.json"

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_client():
    client = EmailClient(
        config=load_json(CONFIG_PATH),
        credentials=load_json(CREDENTIALS_PATH),
        token=load_json(TOKEN_PATH)
    )
    client.authenticate()
    return client

def cmd_organize_inbox(args):
    client = build_client()
    emails = client.get_inbox_emails(max_results=args.max_results)
    client.organize(emails, remove_from_inbox=True)
    print(f"Organized {len(emails)} inbox emails.")

def cmd_organize_earthcaches(args):
    client = build_client()
    client.reorganize_by_condition(
        source_labels=["Email", "Message Center"],
        target_label_name="Earthcaches",
        condition_func=lambda e: e.isFromEarthcache(),
        max_results=args.max_results
    )

def cmd_dashboard(args):
    client = build_client()
    emails = client.get_emails_from_label("Earthcaches", max_results=args.max_results)
    print(f"Fetched {len(emails)} email(s). Opening dashboard…")
    run_dashboard(emails, client=client, port=args.port)

def main():
    parser = argparse.ArgumentParser(prog="geoaware")
    subparsers = parser.add_subparsers(dest="command")

    organize_parser = subparsers.add_parser("organize", help="Organize emails")
    organize_sub = organize_parser.add_subparsers(dest="target")

    inbox_parser = organize_sub.add_parser("inbox", help="Organize inbox emails by filter rules")
    inbox_parser.add_argument("--max-results", type=int, default=50)
    inbox_parser.set_defaults(func=cmd_organize_inbox)

    earthcaches_parser = organize_sub.add_parser("earthcaches", help="Label earthcache emails from Email and Message Center")
    earthcaches_parser.add_argument("--max-results", type=int, default=100)
    earthcaches_parser.set_defaults(func=cmd_organize_earthcaches)

    dashboard_parser = subparsers.add_parser("dashboard", help="Open the Earthcaches email dashboard")
    dashboard_parser.add_argument("--max-results", type=int, default=50)
    dashboard_parser.add_argument("--port", type=int, default=5000)
    dashboard_parser.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
