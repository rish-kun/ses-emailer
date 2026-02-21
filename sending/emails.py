import os
import uuid
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Email:
    def __init__(self, body, subject, sender, recipient, files=[]):
        self.body = body
        self.subject = subject
        self.sender = sender
        self.recipient = recipient
        self.id = uuid.uuid4().hex
        self.files = files

        # self.msg = self.create_message()

    def create_message(self):
        message = MIMEMultipart()
        message["Subject"] = self.subject
        message["From"] = self.sender
        message["To"] = self.recipient
        message.attach(MIMEText(self.body, "plain"))
        self.message = message
        self.attach_files()
        return message

    def create_html_message(self):
        message = MIMEMultipart()
        message["Subject"] = self.subject
        message["From"] = self.sender
        message["To"] = self.recipient
        message.attach(MIMEText(self.body, "html"))
        self.message = message
        self.attach_files()
        return message

    def attach_files(self):
        if not self.message:
            return False
        for file in self.files:
            with open(file, "rb") as f:
                part = MIMEApplication(f.read(), Name=file)
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(file),
                )
                self.message.attach(part)
        return True

    def add_sent(self, email, email_id):
        """
        Add email to sent list for that specific email_id
        """
        pass

    def check_sent(self, email, email_id):
        """
        Check if email has been sent for that specific email_id
        """
        pass


class EmailSent:
    def __init__(self, email: Email, sent_to: list[str], sent_type="bcc"):
        self.email = email
        self.sent_to = sent_to
        if sent_type not in ["bcc", "cc", "to"]:
            raise ValueError("sent_type must be 'bcc', 'cc', or 'to'")
        self.sent_type = sent_type

    def mark_sent(self):
        pass
