import smtplib
from email.mime.multipart import MIMEMultipart
import re

from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel

from config import app_config
from observability.tracing import tracer
from response import Response

blueprint = APIBlueprint('email v2', __name__, url_prefix='/v2/email')
tag = Tag(name="Email v2", description="Rotas para envio de emails", abp_blueprint=blueprint)


class SendEmailBody(BaseModel):
    to = []
    subject: str
    body: str


@blueprint.post('', summary="Envia um email",
                description="Envia um email para um ou mais destinatários com o assunto e corpo informados.",
                responses={"200": Response, "400": Response}, tags=[tag])
def send_email(body: SendEmailBody):
    if not body.to or not body.subject or not body.body:
        return Response(message="email, subject e body não podem ser vazios", status=400).as_return()

    if len(body.to) < 1:
        return Response(message="subject deve ter pelo menos um destinatário", status=400).as_return()

    # validate emails in array with regex
    for email in body.to:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return Response(message=f"o email \"{email}\" é inválido", status=400).as_return()

    recipients = "; ".join(body.to)
    message = MIMEMultipart()
    message['From'] = app_config.email.sender
    message['To'] = recipients
    message['Subject'] = body.subject

    with tracer.start_as_current_span("send_smtp") as span:
        span.set_attribute("email.to", recipients)

        with smtplib.SMTP(app_config.email.host, app_config.email.port) as server:
            try:
                server.starttls()
                server.login(app_config.email.sender, app_config.email.password)
                text = message.as_string()
                server.sendmail(app_config.email.sender, body.to, text)
            except Exception as e:
                return Response(message=str(e), status=500).as_return()

    return Response(message="Email sent successfully", status=200).as_return()
