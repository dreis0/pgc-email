from flask_openapi3 import APIBlueprint, Tag

from response import ResponseWithContent
from datetime import datetime

blueprint = APIBlueprint('healthcheck', __name__, url_prefix='/healthcheck')
tag = Tag(name="Healthcheck", description="Healthcheck da API")


# returns ok with utc date
@blueprint.get('', summary="Healthcheck", description="Healthcheck da API", tags=[tag])
def healthcheck():
    return ResponseWithContent(status=200, content={"now": datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}).as_return()
