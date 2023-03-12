import os
import smtplib
from email.mime.multipart import MIMEMultipart

from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel

from observability.tracing import tracer
from response import Response

blueprint = APIBlueprint('rolldice', __name__, url_prefix='/v1/email',
                         abp_tags=[Tag(name="Email Endpoint")])


class SendEmailBody(BaseModel):
    email: str
    subject: str
    body: str


sender = os.getenv("EMAIL_SENDER")


@blueprint.post('/',
                description=f"Sends an email from {sender} to the specified email address",
                responses={
                    "200": Response,
                    "400": Response,
                })
def send_email(body: SendEmailBody):
    server = os.getenv("EMAIL_SMTP_HOST")
    port = int(os.getenv("EMAIL_SMTP_PORT"))
    password = os.getenv("EMAIL_PASSWORD")

    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = body.email
    message['Subject'] = body.subject

    with tracer.start_as_current_span("send_smtp") as span:
        span.set_attribute("email.to", body.email)

        with smtplib.SMTP(server, port) as server:
            server.starttls()
            server.login(sender, password)
            text = message.as_string()
            server.sendmail(sender, body.email, text)

    return Response(message="Email sent successfully", status=200).as_return()
