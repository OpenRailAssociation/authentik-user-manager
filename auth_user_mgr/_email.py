# SPDX-FileCopyrightText: 2025 DB Systel GmbH
#
# SPDX-License-Identifier: Apache-2.0

"""Class and functions to send an email to the invitees"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from pathlib import Path

from jinja2 import Template


class Mail:  # pylint: disable=too-many-instance-attributes
    """Class for an email with specific template and subject this app will send"""

    def __init__(  # pylint: disable=too-many-positional-arguments, too-many-arguments
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
        self.subject_suffix: str = ""
        self.instance_url: str = ""
        self.instance_title: str = ""

    def create_copy_with_details(
        self,
        subject_suffix: str,
        instance_url: str,
        instance_title: str,
    ):
        """
        Fills in the details of the email template and subject suffix, and return the class if you
        want to create a copy

        :param subject_suffix: Subject suffix for the email
        :param instance_url: URL of the Authentik instance
        :param instance_title: Title of the Authentik instance
        """
        self.subject_suffix = subject_suffix
        self.instance_url = instance_url
        self.instance_title = instance_title

        return self

    def get_inbuilt_template_dir(self) -> Path:
        """Get the inbuilt template directory"""
        # Get the directory of the current module
        module_dir = Path(__file__).resolve().parent

        # Construct the path to the inbuilt templates directory
        template_dir = module_dir / "templates"

        return template_dir

    def read_template(self, message: str, template_file: str) -> str:
        """
        Reads a Jinja2 template from a file and returns it as a string. If the template is empty,
        use the default template from ./templates/<type>.html

        :param message: Message type of the template (e.g., "invitation")
        :param template_file: Path to the Jinja2 template file
        :return: Template string
        """
        # Use default template path if no file path is set
        if not template_file:
            file_path = self.get_inbuilt_template_dir() / f"{message}.html.j2"
        else:
            file_path = Path(file_path).resolve()

        logging.debug("Reading template for '%s' from '%s'", message, file_path)

        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    def send_email(
        self, message: str, recipient: str, template_file: str = "", **template_vars
    ) -> None:
        """
        Sends an email using a Jinja2 template.
        """
        # Read and render the email body using Jinja2
        template_str = self.read_template(message=message, template_file=template_file)
        template = Template(template_str, autoescape=True)
        email_body = template.render(
            instance_url=self.instance_url, instance_title=self.instance_title, **template_vars
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
        logging.debug("Email content: \n%s", msg.as_string())

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
