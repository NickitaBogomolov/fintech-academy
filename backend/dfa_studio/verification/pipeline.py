from dataclasses import dataclass

from dfa_studio.contracts.generator import CONTRACT_NAME, GeneratedContract, token_source
from dfa_studio.domain.checks import Check, CheckGroup, CheckStatus
from dfa_studio.domain.schedule import Schedule
from dfa_studio.domain.spec import IssueSpec
from dfa_studio.verification.evm import run_scenarios
from dfa_studio.verification.slither import SlitherRunner
from dfa_studio.verification.solc import CompilationError, SolidityCompiler


@dataclass(frozen=True)
class ContractVerification:
    checks: list[Check]
    compiler_version: str | None


class ContractVerifier:
    def __init__(self, compiler: SolidityCompiler, slither: SlitherRunner) -> None:
        self._compiler = compiler
        self._slither = slither

    def verify(
        self, spec: IssueSpec, schedule: Schedule, contract: GeneratedContract, static_analysis: bool = True
    ) -> ContractVerification:
        if not self._compiler.available:
            return ContractVerification(
                checks=[
                    Check(
                        id="compile",
                        group=CheckGroup.CONTRACT,
                        title="Компиляция смарт-контракта",
                        status=CheckStatus.SKIPPED,
                        detail="Компилятор Solidity не установлен: выполните npm install в backend/toolchain/solc",
                    )
                ],
                compiler_version=None,
            )
        file_name = f"{CONTRACT_NAME}.sol"
        try:
            compilation = self._compiler.compile(
                {file_name: contract.source, "SettlementToken.sol": token_source()}
            )
        except CompilationError as error:
            return ContractVerification(
                checks=[
                    Check(
                        id="compile",
                        group=CheckGroup.CONTRACT,
                        title="Компиляция смарт-контракта",
                        status=CheckStatus.FAILED,
                        detail="Код не компилируется",
                        rows=[{"Ошибка": message} for message in error.messages],
                    )
                ],
                compiler_version=None,
            )
        compiled = Check(
            id="compile",
            group=CheckGroup.CONTRACT,
            title="Компиляция смарт-контракта",
            status=CheckStatus.PASSED,
            detail=f"solc {compilation.version.split('+')[0]}, предупреждений: {len(compilation.warnings)}",
        )
        checks = [compiled, *run_scenarios(compilation, contract, spec, schedule)]
        if static_analysis:
            checks.append(self._slither.analyze(file_name, contract.source))
        return ContractVerification(checks=checks, compiler_version=compilation.version)
