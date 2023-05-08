import os
import smtplib
from email.mime.multipart import MIMEMultipart

from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel

from observability.tracing import tracer
from response import Response

tag = Tag(name="Email", description="Rotas para envio de emails")
blueprint = APIBlueprint('email', __name__, url_prefix='/v1/email',
                         abp_tags=[tag])


class SendEmailBody(BaseModel):
    email: str
    subject: str
    body: str




@blueprint.post('/',
                summary="Envia um email",
                description=f"Sends an email to the specified email address",
                responses={"200": Response, "400": Response},
                tags=[tag])
def send_email(body: SendEmailBody):
    server = os.getenv("EMAIL_SMTP_HOST")
    port = int(os.getenv("EMAIL_SMTP_PORT"))
    password = os.getenv("EMAIL_PASSWORD")
    sender = os.getenv("EMAIL_SENDER")

    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = body.email
    message['Subject'] = body.subject

    with tracer.start_as_current_span("send_smtp") as span:
        span.set_attribute("email.to", body.email)

        with smtplib.SMTP(server, port) as server:
            try:
                server.starttls()
                server.login(sender, password)
                text = message.as_string()
                server.sendmail(sender, body.email, text)
            except Exception as e:
                return Response(message=str(e), status=500).as_return()

    return Response(message="Email sent successfully", status=200).as_return()
