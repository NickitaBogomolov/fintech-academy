import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

EVM_VERSION = "cancun"


@dataclass(frozen=True)
class CompiledContract:
    abi: list[dict]
    bytecode: str


@dataclass(frozen=True)
class Compilation:
    contracts: dict[str, CompiledContract]
    warnings: list[str]
    version: str


class CompilationError(RuntimeError):
    def __init__(self, messages: list[str]) -> None:
        super().__init__("\n".join(messages))
        self.messages = messages


class SolidityCompiler:
    def __init__(self, toolchain_dir: Path) -> None:
        self._dir = toolchain_dir.resolve()

    @property
    def available(self) -> bool:
        return shutil.which("node") is not None and (self._dir / "node_modules" / "solc").exists()

    def version(self) -> str:
        result = subprocess.run(
            ["node", "-e", "process.stdout.write(require('solc').version())"],
            cwd=self._dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def compile(self, sources: dict[str, str]) -> Compilation:
        request = {
            "language": "Solidity",
            "sources": {name: {"content": content} for name, content in sources.items()},
            "settings": {
                "evmVersion": EVM_VERSION,
                "optimizer": {"enabled": True, "runs": 200},
                "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}},
            },
        }
        result = subprocess.run(
            ["node", "compile.js"],
            cwd=self._dir,
            input=json.dumps(request),
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        output = json.loads(result.stdout)
        diagnostics = output.get("errors", [])
        errors = [item["formattedMessage"] for item in diagnostics if item["severity"] == "error"]
        if errors:
            raise CompilationError(errors)
        contracts = {
            name: CompiledContract(abi=item["abi"], bytecode=item["evm"]["bytecode"]["object"])
            for file_contracts in output["contracts"].values()
            for name, item in file_contracts.items()
        }
        warnings = [item["formattedMessage"] for item in diagnostics if item["severity"] == "warning"]
        return Compilation(contracts=contracts, warnings=warnings, version=self.version())
