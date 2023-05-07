from flask import jsonify
from pydantic import BaseModel, Field


class Response(BaseModel):
    message: str = Field("ok", description="The message of the response")
    status: int = Field(0, description="The status code of the response")

    def as_return(self):
        return jsonify(self.dict()), self.status


class ResponseWithContent(Response):
    content: dict = Field({}, description="The content of the response")
