import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from dfa_studio.domain.checks import Check, CheckGroup, CheckStatus

IMPACT_LABELS = {
    "High": "Высокий",
    "Medium": "Средний",
    "Low": "Низкий",
    "Informational": "Информационный",
    "Optimization": "Оптимизация",
}

DETECTOR_LABELS = {
    "calls-loop": "Внешний вызов внутри цикла: при большом числе держателей выплату стоит разбить на части",
    "timestamp": "Условия зависят от времени блока: допустимо для дат выплат с точностью до минут",
    "reentrancy-eth": "Повторный вход с выводом средств",
    "reentrancy-no-eth": "Повторный вход с изменением состояния",
    "reentrancy-benign": "Повторный вход без влияния на средства",
    "reentrancy-events": "Событие после внешнего вызова",
    "low-level-calls": "Низкоуровневый вызов",
    "unchecked-transfer": "Не проверяется результат перевода",
    "arbitrary-send-erc20": "Перевод токенов с произвольного адреса",
    "costly-loop": "Дорогая операция в цикле",
    "naming-convention": "Нарушение соглашения об именовании",
    "solc-version": "Версия компилятора",
    "missing-zero-check": "Нет проверки нулевого адреса",
    "cache-array-length": "Длину массива можно кэшировать",
    "dead-code": "Неиспользуемый код",
    "too-many-digits": "Длинные числовые литералы",
}

BLOCKING = {"High", "Medium"}


class SlitherRunner:
    def __init__(self, solc_wrapper: Path, enabled: bool = True) -> None:
        self._solc = solc_wrapper.resolve()
        self._enabled = enabled

    @property
    def available(self) -> bool:
        return self._enabled and shutil.which("slither") is not None and self._solc.exists()

    def analyze(self, file_name: str, source: str) -> Check:
        if not self.available:
            return Check(
                id="slither",
                group=CheckGroup.ANALYSIS,
                title="Статический анализ Slither",
                status=CheckStatus.SKIPPED,
                detail="Slither не установлен в этом окружении",
            )
        with tempfile.TemporaryDirectory() as workdir:
            path = Path(workdir) / file_name
            path.write_text(source, encoding="utf-8")
            result = subprocess.run(
                ["slither", file_name, "--solc", str(self._solc), "--json", "-"],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=180,
            )
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            return Check(
                id="slither",
                group=CheckGroup.ANALYSIS,
                title="Статический анализ Slither",
                status=CheckStatus.SKIPPED,
                detail="Slither завершился без отчёта",
            )
        if not report.get("success"):
            return Check(
                id="slither",
                group=CheckGroup.ANALYSIS,
                title="Статический анализ Slither",
                status=CheckStatus.FAILED,
                detail=str(report.get("error") or "Ошибка анализа"),
            )
        return summarize(report.get("results", {}).get("detectors", []))


def summarize(detectors: list[dict]) -> Check:
    rows = []
    impacts = set()
    for item in detectors:
        impact = item.get("impact", "Informational")
        impacts.add(impact)
        check = item.get("check", "")
        description = DETECTOR_LABELS.get(check) or item.get("description", "").splitlines()[0]
        rows.append(
            {"Уровень": IMPACT_LABELS.get(impact, impact), "Детектор": check, "Описание": description}
        )
    order = list(IMPACT_LABELS.values())
    rows.sort(key=lambda row: order.index(row["Уровень"]) if row["Уровень"] in order else len(order))
    if impacts & BLOCKING:
        status, detail = CheckStatus.FAILED, "Найдены уязвимости высокого или среднего уровня"
    elif "Low" in impacts:
        status, detail = CheckStatus.WARNING, "Критичных находок нет, есть замечания низкого уровня"
    else:
        status, detail = CheckStatus.PASSED, "Критичных находок нет"
    return Check(
        id="slither",
        group=CheckGroup.ANALYSIS,
        title="Статический анализ Slither",
        status=status,
        detail=f"{detail}. Всего замечаний: {len(rows)}",
        rows=rows,
    )
