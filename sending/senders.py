import os
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
from dotenv import load_dotenv
from emails import Email

from config.settings import format_source_email, get_email_address


class EmailSender:
    def __init__(self, reply_to, env_file) -> None:
        self.sender = None
        self.reply_to = reply_to
        self.to = reply_to
        self.env_file = env_file

    def load_config(self, env_file):
        load_dotenv(env_file)
        return (
            os.getenv("AWS_ACCESS_KEY_ID"),
            os.getenv("AWS_SECRET_ACCESS_KEY"),
            os.getenv("REGION"),
            os.getenv("SOURCE_EMAIL", "test@example.com"),
        )

    def setup_client(self, env_file=None):
        if not env_file:
            env_file = self.env_file
        AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION, SOURCE_EMAIL = (
            self.load_config(env_file)
        )
        self.source_email = SOURCE_EMAIL
        ses_client = boto3.client(
            "sesv2",
            region_name=REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        return ses_client

    def send_bcc_plain_mail(
        self,
        recipients: list,
        email: Email,
        etype: str = "bcc",
    ):
        if etype not in ["bcc", "cc", "to"]:
            raise ValueError("Invalid type")
        ses_client = self.setup_client()
        if not email.check_sent(recipients, email.id):
            email.add_sent(recipients, email.id)
            from_address = format_source_email(self.source_email, self.sender or "")
            ses_client.send_email(
                FromEmailAddress=from_address,
                Destination={
                    "BccAddresses": recipients,
                    "ToAddresses": [
                        get_email_address(self.source_email)
                        if self.to == self.source_email
                        else self.to
                    ],
                },
                Content={
                    "Raw": {
                        "Data": email.create_message().as_bytes(),
                    }
                },
            )

    def send_bcc_html_mail(self, recipient, subject, body, files=[]):
        pass


class MassEmailSender(EmailSender):
    def __init__(self, sender, id, reply_to, delay=60, env_file=None):
        self.sender = sender
        self.id = id
        self.reply_to = reply_to
        self.to = reply_to
        self.delay = delay

    def send_batch_emails(
        self,
        recipients,
        batch_size: int = 50,
        delay: int = 60,
        subject: str = "",
        body: str = "",
        email_type: str = "",
        files: list[str] = [],
        bcc: bool = True,
        cc: bool = False,
    ):
        total_batches = len(recipients) // batch_size + (
            1 if len(recipients) % batch_size else 0
        )
        print(f"Total recipients: {len(recipients)}, Total batches: {total_batches}")
        input("Press Enter to start sending emails...")
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = self.sender
            msg["To"] = self.to
            msg["Reply-To"] = self.reply_to
            if bcc:
                msg["Bcc"] = ", ".join(batch)
            elif cc:
                msg["Cc"] = ", ".join(batch)
            msg_body = MIMEMultipart("alternative")
            msg_body.attach(MIMEText(body, "html"))
            msg.attach(msg_body)
            if files:
                for file in files:
                    with open("./files/" + file, "rb") as f:
                        part = MIMEApplication(f.read(), Name=file)
                        part.add_header(
                            "Content-Disposition",
                            "attachment",
                            filename=os.path.basename(file),
                        )
                        msg.attach(part)

            print(f"Sending batch {batch_num}/{total_batches} ({len(batch)} emails)")

            try:
                self.send_bcc_plain_mail(batch, msg)
                if i + batch_size < len(recipients):
                    print(f"Waiting {delay} seconds before next batch...")
                    time.sleep(delay)
            except Exception as e:
                print(f"Error in batch {batch_num}: {str(e)}")
