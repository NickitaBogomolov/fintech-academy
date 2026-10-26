import re
from dataclasses import dataclass
from datetime import date
from importlib import resources
from pathlib import Path

from jinja2 import Environment, StrictUndefined, TemplateError, meta

from dfa_studio.documents import formatting
from dfa_studio.domain.schedule import Schedule
from dfa_studio.domain.spec import IssueSpec

CONTEXT_NAMES = frozenset({"spec", "issuer", "schedule", "operator", "today"})
TEMPLATE_SUFFIX = ".md.j2"
META_PATTERN = re.compile(r"\{#-?\s*(title|description):\s*(.+?)\s*-?#\}")


@dataclass(frozen=True)
class Operator:
    name: str
    ogrn: str
    website: str


@dataclass(frozen=True)
class TemplateInfo:
    id: str
    title: str
    description: str
    builtin: bool
    source: str
    variables: list[str]


class TemplateValidationError(ValueError):
    pass


def _environment() -> Environment:
    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True, autoescape=False)
    env.filters.update(
        money=formatting.money,
        money_words=formatting.money_words,
        int_words=formatting.int_words,
        percent=formatting.percent,
        percent_words=formatting.percent_words,
        date_ru=formatting.date_ru,
        date_words=formatting.date_words,
        frequency_label=formatting.frequency_label,
    )
    return env


ENV = _environment()


def _metadata(source: str) -> dict[str, str]:
    return {key: value for key, value in META_PATTERN.findall(source)}


def _variables(source: str) -> list[str]:
    return sorted(set(re.findall(r"\b(?:spec|issuer|schedule|operator)\.[a-z_]+", source)))


class TemplateStore:
    def __init__(self, user_dir: Path) -> None:
        self._user_dir = user_dir
        self._user_dir.mkdir(parents=True, exist_ok=True)

    def _builtin(self) -> dict[str, str]:
        folder = resources.files("dfa_studio.documents").joinpath("templates")
        return {
            item.name.removesuffix(TEMPLATE_SUFFIX): item.read_text(encoding="utf-8")
            for item in folder.iterdir()
            if item.name.endswith(TEMPLATE_SUFFIX)
        }

    def _user(self) -> dict[str, str]:
        return {
            path.name.removesuffix(TEMPLATE_SUFFIX): path.read_text(encoding="utf-8")
            for path in sorted(self._user_dir.glob(f"*{TEMPLATE_SUFFIX}"))
        }

    def _info(self, template_id: str, source: str, builtin: bool) -> TemplateInfo:
        metadata = _metadata(source)
        return TemplateInfo(
            id=template_id,
            title=metadata.get("title", template_id),
            description=metadata.get("description", ""),
            builtin=builtin,
            source=source,
            variables=_variables(source),
        )

    def list(self) -> list[TemplateInfo]:
        builtin = [self._info(key, source, True) for key, source in self._builtin().items()]
        user = [self._info(key, source, False) for key, source in self._user().items()]
        return builtin + user

    def get(self, template_id: str) -> TemplateInfo:
        for info in self.list():
            if info.id == template_id:
                return info
        raise KeyError(template_id)

    def save(self, template_id: str, source: str) -> TemplateInfo:
        if not re.fullmatch(r"[a-z0-9_-]{3,64}", template_id):
            raise TemplateValidationError("идентификатор: латиница, цифры, «-» и «_», от 3 до 64 символов")
        if template_id in self._builtin():
            raise TemplateValidationError("встроенный шаблон нельзя перезаписать")
        validate_template(source)
        (self._user_dir / f"{template_id}{TEMPLATE_SUFFIX}").write_text(source, encoding="utf-8")
        return self._info(template_id, source, False)

    def delete(self, template_id: str) -> None:
        path = self._user_dir / f"{template_id}{TEMPLATE_SUFFIX}"
        if not path.exists():
            raise KeyError(template_id)
        path.unlink()


def validate_template(source: str) -> None:
    try:
        parsed = ENV.parse(source)
    except TemplateError as error:
        raise TemplateValidationError(f"синтаксическая ошибка: {error}") from error
    unknown = meta.find_undeclared_variables(parsed) - CONTEXT_NAMES
    if unknown:
        names = ", ".join(sorted(unknown))
        raise TemplateValidationError(f"неизвестные переменные: {names}")


def render_document(source: str, spec: IssueSpec, schedule: Schedule, operator: Operator, today: date) -> str:
    try:
        template = ENV.from_string(source)
        text = template.render(
            spec=spec, issuer=spec.issuer, schedule=schedule, operator=operator, today=today
        )
    except TemplateError as error:
        raise TemplateValidationError(f"ошибка при заполнении шаблона: {error}") from error
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
