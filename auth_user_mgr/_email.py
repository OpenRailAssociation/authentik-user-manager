"""Class and functions to send an email to the invitees"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

from jinja2 import Template


class Mail:
    """Class for an email with specific template and subject this app will send"""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: str | int,
        smtp_user: str,
        smtp_password: str,
        smtp_starttls: bool,
        smtp_from: str,
        dry: bool,
    ):
        self.smtp_server: str = smtp_server
        self.smtp_port: str | int = smtp_port
        self.smtp_user: str = smtp_user
        self.smtp_password: str = smtp_password
        self.smtp_starttls: bool = smtp_starttls
        self.smtp_from: str = smtp_from
        self.dry: bool = dry
        self.template: str = ""
        self.subject_suffix: str = ""
        self.instance_url: str = ""
        self.instance_title: str = ""

    def create_copy_with_details(
        self, template: str, subject_suffix: str, instance_url: str, instance_title: str
    ):
        """
        Fills in the details of the email template and subject suffix, and return the class if you
        want to create a copy

        :param template: Path to the Jinja2 template file
        :param subject_suffix: Subject suffix for the email
        :param instance_url: URL of the Authentik instance
        :param instance_title: Title of the Authentik instance
        """
        self.template = template
        self.subject_suffix = subject_suffix
        self.instance_url = instance_url
        self.instance_title = instance_title

        return self

    def read_template(self, file_path):
        """
        Reads a Jinja2 template from a file and returns it as a string.

        :param file_path: Path to the Jinja2 template file
        :return: Template string
        """
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    def send_email(self, recipient: str, link: str) -> None:
        """
        Sends an email using a Jinja2 template.
        """
        # Read and render the email body using Jinja2
        template_str = self.read_template(self.template)
        template = Template(template_str, autoescape=True)
        email_body = template.render(
            link=link, instance_url=self.instance_url, instance_title=self.instance_title
        )

        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = self.smtp_from
        msg["To"] = recipient
        msg["Subject"] = f"{self.instance_title}: {self.subject_suffix}"
        msg["Message-ID"] = make_msgid(idstring="auth-invite", domain="localhost")
        msg["Date"] = formatdate(localtime=True)

        # Attach the email body as HTML
        msg.attach(MIMEText(email_body, "html"))

        if self.dry:
            logging.info("Dry run, not sending email to %s", recipient)
            return

        try:
            # Send the email
            with smtplib.SMTP(self.smtp_server, int(self.smtp_port)) as server:
                if self.smtp_starttls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_from, recipient, msg.as_string())
            logging.info("Email sent to %s", recipient)

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Failed to send email: {e}")
