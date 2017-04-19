import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Mailer:

    def send_email(self, server, port, username, password, from_email, to_email, subject, html_message, plain_message):
        server = smtplib.SMTP(server, port)
        server.starttls()
        server.login(username, password)

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        # Record the MIME types of both parts - text/plain and text/html.
        # part1 = MIMEText(message, 'plain')
        part1 = MIMEText(plain_message, 'plain')
        part2 = MIMEText(html_message, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)

        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()