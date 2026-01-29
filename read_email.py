from googleapiclient.errors import HttpError
from email_api_setup import get_gmail_service
import json
import base64
import re
import os

HISTORY_FILE = "history_id.txt"


def load_history_id():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return f.read().strip()
    return None


def save_history_id(history_id):
    with open(HISTORY_FILE, "w") as f:
        f.write(history_id)


def decode_base64url(encoded_string: str) -> str:
    if not encoded_string:
        return ""
    # pad
    encoded_string += "=" * ((4 - len(encoded_string) % 4) % 4)
    decoded_bytes = base64.urlsafe_b64decode(encoded_string.encode("utf-8"))
    return decoded_bytes.decode("utf-8", errors="replace").rstrip()


def helper_write(msg_data):
    try:
        with open(f"data{i}.json", "w", encoding="utf-8") as json_file:
            json.dump(msg_data, json_file, indent=4)
    except IOError as e:
        print(f"Error writing to file: {e}")


def main():
    emails = []
    try:
        service = get_gmail_service()

        history_id = load_history_id()

        if not history_id:
            profile = service.users().getProfile(userId="me").execute()
            save_history_id(profile["historyId"])
            print("History baseline saved. Run again.")
            return

        history = (
            service.users()
            .history()
            .list(userId="me", startHistoryId=history_id, historyTypes=["messageAdded"])
            .execute()
        )

        messages = []

        for h in history.get("history", []):
            for m in h.get("messagesAdded", []):
                messages.append(m["message"])

        print("Messages:")
        i = 0
        for message in messages:
            i += 1
            print(f'Message ID: {message["id"]}')
            msg_data = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )

            email = {}
            headers = msg_data["payload"]["headers"]

            for header in headers:
                if header["name"] == "Subject":
                    email["subject"] = header["value"]
                if header["name"] == "From":
                    email["from"] = header["value"]
                if header["name"] == "Date":
                    email["date"] = header["value"]

                if "subject" in email and "from" in email and "date" in email:
                    break

            message_content = ""
            attachment = {}
            if "parts" in msg_data["payload"]:
                for part in msg_data["payload"]["parts"]:
                    if part["mimeType"] == "text/plain":
                        message_content = decode_base64url(part["body"]["data"])
                    if part["mimeType"] == "multipart/alternative":
                        another_parts = part["parts"]
                        for another_part in another_parts:
                            if another_part["mimeType"] == "text/plain":
                                message_content = decode_base64url(
                                    another_part["body"]["data"]
                                )
                                break
                    if re.match(r"^application/.*", part["mimeType"]):
                        attachment["filename"] = part["filename"]
                        attachment["attachmentData"] = (
                            service.users()
                            .messages()
                            .attachments()
                            .get(
                                userId="me",
                                messageId=message["id"],
                                id=part["body"]["attachmentId"],
                            )
                            .execute()
                        )

            email["text_content"] = message_content
            email["attachemnt"] = attachment

            emails.append(email)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

    save_history_id(history["historyId"])

    if not emails:
        print("No new emails.")
    else:
        for email in emails:
            print(email)


if __name__ == "__main__":
    main()
