from flask import jsonify
from pydantic import BaseModel, Field


class Response(BaseModel):
    message: str = Field("ok", description="Mensagem da resposta")
    status: int = Field(0, description="Código de status da resposta")

    def as_return(self):
        if self.status == 200:
            return None, self.status
        return jsonify(self.dict()), self.status


class ResponseWithContent(Response):
    content: dict = Field({}, description="Conteúdo da resposta")
