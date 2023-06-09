import re
import smtplib
from email.mime.multipart import MIMEMultipart

from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel

from config import app_config
from observability.tracing import tracer
from response import Response

tag = Tag(name="Email v1", description="Rotas para envio de emails")
blueprint = APIBlueprint('email', __name__, url_prefix='/v1/email',
                         abp_tags=[tag])


class SendEmailBody(BaseModel):
    email: str
    subject: str
    body: str


@blueprint.post('',
                summary="Envia um email",
                description=f"Envia um email para o destinatário com o assunto e corpo informados.",
                responses={"200": Response, "400": Response},
                tags=[tag])
def send_email(body: SendEmailBody):
    if not body.email or not body.subject or not body.body:
        return Response(message="email, subject e body não podem ser vazios", status=400).as_return()

    if not re.match(r"[^@]+@[^@]+\.[^@]+", body.email):
        return Response(message="email inválido", status=400).as_return()

    message = MIMEMultipart()
    message['From'] = app_config.email.sender
    message['To'] = body.email
    message['Subject'] = body.subject

    with tracer.start_as_current_span("send_smtp") as span:
        span.set_attribute("email.to", body.email)

        with smtplib.SMTP(app_config.email.host, app_config.email.port) as server:
            try:
                server.starttls()
                server.login(app_config.email.sender, app_config.email.password)
                text = message.as_string()
                server.sendmail(app_config.email.sender, body.email, text)
            except Exception as e:
                return Response(message=str(e), status=500).as_return()

    return Response(message="Email sent successfully", status=200).as_return()
