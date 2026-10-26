import json
from functools import cache
from importlib import resources
from typing import Annotated, Any
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from dfa_studio.contracts.generator import FAULT_LABELS, ContractFault
from dfa_studio.documents.docx_export import markdown_to_docx
from dfa_studio.documents.render import TemplateValidationError
from dfa_studio.domain.builder import SpecError
from dfa_studio.domain.fields import FIELDS, GROUPS
from dfa_studio.extraction.drafting import Draft
from dfa_studio.registry import find_issuer, list_issuers
from dfa_studio.service import IssueRequest, Studio
from dfa_studio.settings import get_settings


class DraftRequest(BaseModel):
    text: str
    inn: str | None = None
    answers: dict[str, Any] | None = None


class TemplateRequest(BaseModel):
    id: str
    source: str


class PreviewRequest(BaseModel):
    source: str


class FaultRequest(BaseModel):
    fault: ContractFault


@cache
def get_studio() -> Studio:
    return Studio(get_settings())


StudioDep = Annotated[Studio, Depends(get_studio)]


def _examples() -> list[dict[str, str]]:
    raw = resources.files("dfa_studio.data").joinpath("examples.json").read_text(encoding="utf-8")
    return json.loads(raw)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ЦФА Студия", version="0.1.0")
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"]
    )

    @app.exception_handler(SpecError)
    async def spec_error(_: Request, error: SpecError) -> JSONResponse:
        return JSONResponse(
            status_code=422, content={"detail": "Проверьте параметры", "fields": error.errors}
        )

    @app.exception_handler(TemplateValidationError)
    async def template_error(_: Request, error: TemplateValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @app.exception_handler(KeyError)
    async def not_found(_: Request, error: KeyError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": f"Не найдено: {error.args[0]}"})

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/meta")
    def meta(studio: StudioDep) -> dict[str, Any]:
        return {
            "groups": GROUPS,
            "fields": [field.model_dump(mode="json") for field in FIELDS],
            "examples": _examples(),
            "issuers": [issuer.model_dump(mode="json") for issuer in list_issuers()],
            "faults": [{"value": fault.value, "label": label} for fault, label in FAULT_LABELS.items()],
            "provider": studio.provider_label,
        }

    @app.get("/api/system")
    def system(studio: StudioDep) -> dict[str, Any]:
        return studio.system()

    @app.get("/api/registry/{inn}")
    def registry(inn: str) -> dict[str, Any]:
        issuer = find_issuer(inn)
        if issuer is None:
            raise HTTPException(status_code=404, detail="Эмитент не найден в реестре")
        return issuer.model_dump(mode="json")

    @app.post("/api/drafts")
    def draft(request: DraftRequest, studio: StudioDep) -> Draft:
        return studio.draft(request.text, request.inn, request.answers)

    @app.post("/api/issues")
    def create_issue(request: IssueRequest, studio: StudioDep) -> dict[str, Any]:
        return studio.create_issue(request)

    @app.get("/api/issues")
    def list_issues(studio: StudioDep) -> list[dict[str, Any]]:
        return studio.list_issues()

    @app.get("/api/issues/{issue_id}")
    def get_issue(issue_id: str, studio: StudioDep) -> dict[str, Any]:
        return studio.get_issue(issue_id)

    @app.post("/api/issues/{issue_id}/faults")
    def run_fault(issue_id: str, request: FaultRequest, studio: StudioDep) -> dict[str, Any]:
        return studio.run_fault(issue_id, request.fault)

    @app.get("/api/issues/{issue_id}/files/{name}")
    def download(issue_id: str, name: str, studio: StudioDep) -> Response:
        package = studio.get_issue(issue_id)
        number = package["spec"]["issue_number"]
        files = {
            "decision.docx": (
                lambda: markdown_to_docx(package["document"]),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                f"Решение о выпуске {number}.docx",
            ),
            "decision.md": (
                lambda: package["document"].encode(),
                "text/markdown",
                f"Решение о выпуске {number}.md",
            ),
            "contract.sol": (
                lambda: package["contract"]["source"].encode(),
                "text/plain",
                f"{package['contract']['name']}-{number}.sol",
            ),
            "package.json": (
                lambda: json.dumps(package, ensure_ascii=False, indent=2).encode(),
                "application/json",
                f"Пакет выпуска {number}.json",
            ),
        }
        if name not in files:
            raise HTTPException(status_code=404, detail="Файл не найден")
        build, media_type, filename = files[name]
        return Response(
            content=build(),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
        )

    @app.get("/api/templates")
    def templates(studio: StudioDep) -> list[dict[str, Any]]:
        return [vars(info) for info in studio.templates.list()]

    @app.get("/api/templates/{template_id}")
    def template(template_id: str, studio: StudioDep) -> dict[str, Any]:
        return vars(studio.templates.get(template_id))

    @app.post("/api/templates")
    def save_template(request: TemplateRequest, studio: StudioDep) -> dict[str, Any]:
        studio.sample_document(request.source)
        return vars(studio.templates.save(request.id, request.source))

    @app.post("/api/templates/preview")
    def preview_template(request: PreviewRequest, studio: StudioDep) -> dict[str, str]:
        return {"document": studio.sample_document(request.source)}

    @app.delete("/api/templates/{template_id}")
    def delete_template(template_id: str, studio: StudioDep) -> dict[str, str]:
        studio.templates.delete(template_id)
        return {"status": "deleted"}

    @app.get("/api/metrics")
    def metrics(studio: StudioDep) -> dict[str, Any]:
        return studio.metrics()

    @app.post("/api/benchmark")
    def benchmark(studio: StudioDep) -> dict[str, Any]:
        return studio.run_benchmark()

    return app


app = create_app()
