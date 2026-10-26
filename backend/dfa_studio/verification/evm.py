from collections.abc import Callable
from dataclasses import dataclass
from datetime import time
from decimal import Decimal

from eth_tester import EthereumTester, PyEVMBackend
from eth_tester.exceptions import TransactionFailed
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError, Web3RPCError

from dfa_studio.contracts.generator import CONTRACT_NAME, TOKEN_NAME, GeneratedContract, kopecks, timestamp
from dfa_studio.documents.formatting import date_ru, group_digits, money
from dfa_studio.domain.checks import Check, CheckGroup, CheckStatus
from dfa_studio.domain.schedule import Schedule
from dfa_studio.domain.spec import InvestorAccess, IssueSpec
from dfa_studio.verification.solc import Compilation

REVERTS = (ContractLogicError, TransactionFailed, Web3RPCError)
HOUR = 3600


@dataclass
class _Chain:
    tester: EthereumTester
    w3: Web3
    token: Contract
    asset: Contract
    operator: str
    issuer: str
    investors: list[str]
    outsider: str

    def travel(self, moment: int) -> None:
        current = self.w3.eth.get_block("latest")["timestamp"]
        if moment > current:
            self.tester.time_travel(moment)

    def send(self, call, sender: str) -> None:
        receipt = self.w3.eth.wait_for_transaction_receipt(call.transact({"from": sender, "gas": 5_000_000}))
        if receipt.status != 1:
            raise TransactionFailed("transaction reverted")

    def reverts(self, action: Callable[[], None], rollback: bool = True) -> bool:
        snapshot = self.tester.take_snapshot()
        try:
            action()
        except REVERTS:
            return True
        if rollback:
            self.tester.revert_to_snapshot(snapshot)
        return False

    def balance(self, account: str) -> int:
        return self.token.functions.balanceOf(account).call()


def _deploy(compilation: Compilation, start: int) -> _Chain:
    backend = PyEVMBackend(
        genesis_parameters=PyEVMBackend.generate_genesis_params(overrides={"timestamp": start})
    )
    tester = EthereumTester(backend)
    w3 = Web3(Web3.EthereumTesterProvider(tester))
    accounts = w3.eth.accounts
    operator, issuer, outsider, *investors = accounts[:7]

    def deploy(name: str, *args) -> Contract:
        compiled = compilation.contracts[name]
        factory = w3.eth.contract(abi=compiled.abi, bytecode=compiled.bytecode)
        receipt = w3.eth.wait_for_transaction_receipt(
            factory.constructor(*args).transact({"from": operator, "gas": 8_000_000})
        )
        return w3.eth.contract(address=receipt.contractAddress, abi=compiled.abi)

    token = deploy(TOKEN_NAME)
    asset = deploy(CONTRACT_NAME, token.address, operator, issuer)
    return _Chain(tester, w3, token, asset, operator, issuer, investors, outsider)


def _split(total: int, parts: int) -> list[int]:
    base, rest = divmod(total, parts)
    return [base + (1 if index < rest else 0) for index in range(parts) if base or index < rest]


def _subscribe_all(chain: _Chain, quantities: list[int], price: int) -> None:
    for investor, quantity in zip(chain.investors, quantities, strict=False):
        chain.send(chain.token.functions.mint(investor, quantity * price), chain.operator)
        chain.send(chain.token.functions.approve(chain.asset.address, quantity * price), investor)
        chain.send(chain.asset.functions.subscribe(quantity), investor)


def _check(
    check_id: str, title: str, ok: bool, detail: str, rows: list[dict[str, str]] | None = None
) -> Check:
    return Check(
        id=check_id,
        group=CheckGroup.CONTRACT,
        title=title,
        status=CheckStatus.PASSED if ok else CheckStatus.FAILED,
        detail=detail,
        rows=rows or [],
    )


def _primary_scenario(
    compilation: Compilation, contract: GeneratedContract, spec: IssueSpec, schedule: Schedule
) -> list[Check]:
    book_start = timestamp(spec.book_start, time(9, 0))
    chain = _deploy(compilation, book_start - 2 * HOUR)
    price = kopecks(spec.price)
    asset = chain.asset.functions
    checks: list[Check] = []

    for investor in chain.investors:
        chain.send(asset.setInvestor(investor, True, True), chain.operator)
    if spec.investors is InvestorAccess.QUALIFIED_ONLY:
        chain.send(asset.setInvestor(chain.outsider, True, False), chain.operator)

    chain.send(chain.token.functions.mint(chain.investors[0], price), chain.operator)
    chain.send(chain.token.functions.approve(chain.asset.address, price), chain.investors[0])
    early = chain.reverts(lambda: chain.send(asset.subscribe(1), chain.investors[0]))
    checks.append(
        _check(
            "book-window",
            "Заявки принимаются только в период сбора",
            early,
            f"Заявка до 09:00 {date_ru(spec.book_start)} отклонена"
            if early
            else "Заявка до начала сбора принята",
        )
    )

    chain.travel(book_start + 60)
    outsider_title = (
        "Неквалифицированный инвестор не может купить ЦФА"
        if spec.investors is InvestorAccess.QUALIFIED_ONLY
        else "Неидентифицированное лицо не может купить ЦФА"
    )
    chain.send(chain.token.functions.mint(chain.outsider, price), chain.operator)
    chain.send(chain.token.functions.approve(chain.asset.address, price), chain.outsider)
    blocked = chain.reverts(lambda: chain.send(asset.subscribe(1), chain.outsider))
    checks.append(
        _check("eligibility", outsider_title, blocked, "Заявка отклонена" if blocked else "Заявка принята")
    )

    total = min(spec.max_quantity, max(spec.min_quantity, len(chain.investors)))
    quantities = _split(total, len(chain.investors))
    _subscribe_all(chain, quantities, price)

    remaining = spec.max_quantity - total
    over = chain.reverts(lambda: chain.send(asset.subscribe(remaining + 1), chain.investors[0]))
    checks.append(
        _check(
            "max-quantity",
            "Нельзя разместить больше максимального объёма",
            over,
            f"Заявка сверх {group_digits(spec.max_quantity)} ЦФА отклонена"
            if over
            else "Лимит не соблюдается",
        )
    )

    chain.travel(timestamp(spec.issue_date))
    issuer_before = chain.balance(chain.issuer)
    chain.send(asset.finalize(), chain.operator)
    proceeds = chain.balance(chain.issuer) - issuer_before
    expected_proceeds = total * price
    checks.append(
        _check(
            "proceeds",
            "Деньги инвесторов переданы эмитенту после размещения",
            asset.phase().call() == 1 and proceeds == expected_proceeds,
            f"Получено {money(Decimal(proceeds) / 100)} ₽ за {group_digits(total)} ЦФА",
        )
    )

    stranger_transfer = chain.reverts(
        lambda: chain.send(asset.transfer(chain.outsider, 1), chain.investors[0])
    )
    if quantities[0] > 1:
        chain.send(asset.transfer(chain.investors[1], 1), chain.investors[0])
        quantities[0] -= 1
        quantities[1] += 1
    checks.append(
        _check(
            "transfer-eligibility",
            "ЦФА можно передать только допущенному инвестору",
            stranger_transfer,
            "Передача неподходящему лицу отклонена" if stranger_transfer else "Передача прошла",
        )
    )

    holdings = dict(zip(chain.investors, quantities, strict=False))
    mismatches: list[dict[str, str]] = []
    premature: list[dict[str, str]] = []
    for period in schedule.periods:
        due = timestamp(period.payment_date)
        chain.travel(due - HOUR)
        expected_per_asset = kopecks(period.payment)
        funding = expected_per_asset * total
        chain.send(chain.token.functions.mint(chain.asset.address, funding), chain.operator)
        if not chain.reverts(lambda: chain.send(asset.payNextPeriod(), chain.operator), rollback=False):
            premature.append({"Период": str(period.number), "Дата по графику": date_ru(period.payment_date)})
            continue
        chain.travel(due)
        before = {holder: chain.balance(holder) for holder in holdings}
        chain.send(asset.payNextPeriod(), chain.operator)
        for holder, quantity in holdings.items():
            received = chain.balance(holder) - before[holder]
            expected = expected_per_asset * quantity
            if received != expected:
                mismatches.append(
                    {
                        "Период": str(period.number),
                        "Инвестор": f"{holder[:6]}…{holder[-4:]}",
                        "По решению, ₽": money(Decimal(expected) / 100),
                        "По контракту, ₽": money(Decimal(received) / 100),
                        "Разница, ₽": money(Decimal(expected - received) / 100),
                    }
                )

    checks.append(
        _check(
            "no-early-payments",
            "Выплаты не происходят раньше дат графика",
            not premature,
            "Попытка выплаты за час до даты отклонена в каждом периоде"
            if not premature
            else "Контракт позволил выплатить раньше даты из решения о выпуске",
            premature,
        )
    )
    checks.append(
        _check(
            "payments-match-document",
            "Суммы выплат совпадают с решением о выпуске",
            not mismatches,
            f"Проверено периодов: {len(schedule.periods)}, держателей: {len(holdings)}"
            if not mismatches
            else f"Расхождений: {len(mismatches)}",
            mismatches,
        )
    )
    redeemed = asset.phase().call() == 3 and asset.totalSupply().call() == 0
    checks.append(
        _check(
            "redemption",
            "Номинал погашен, выпуск закрыт",
            redeemed,
            f"Погашение {date_ru(schedule.periods[-1].payment_date)}" if redeemed else "Выпуск не закрыт",
        )
    )
    return checks


def _funding_scenario(compilation: Compilation, spec: IssueSpec, schedule: Schedule) -> Check:
    chain = _deploy(compilation, timestamp(spec.book_start, time(9, 0)) + 60)
    price = kopecks(spec.price)
    for investor in chain.investors:
        chain.send(chain.asset.functions.setInvestor(investor, True, True), chain.operator)
    total = min(spec.max_quantity, max(spec.min_quantity, len(chain.investors)))
    _subscribe_all(chain, _split(total, len(chain.investors)), price)
    chain.travel(timestamp(spec.issue_date))
    chain.send(chain.asset.functions.finalize(), chain.operator)
    chain.travel(timestamp(schedule.periods[0].payment_date))
    blocked = chain.reverts(lambda: chain.send(chain.asset.functions.payNextPeriod(), chain.operator))
    return _check(
        "insufficient-funds",
        "Без денег эмитента выплата не проходит частично",
        blocked,
        "Выплата отклонена целиком, инвесторы не получают неравные суммы"
        if blocked
        else "Контракт провёл выплату без обеспечения",
    )


def _failed_issue_scenario(compilation: Compilation, spec: IssueSpec) -> Check:
    title = "Если минимальный объём не набран, деньги возвращаются"
    if spec.min_quantity <= 1:
        return Check(
            id="refund",
            group=CheckGroup.CONTRACT,
            title=title,
            status=CheckStatus.SKIPPED,
            detail="Минимальный объём равен одному ЦФА",
        )
    chain = _deploy(compilation, timestamp(spec.book_start, time(9, 0)) + 60)
    price = kopecks(spec.price)
    for investor in chain.investors:
        chain.send(chain.asset.functions.setInvestor(investor, True, True), chain.operator)
    quantities = _split(spec.min_quantity - 1, len(chain.investors))
    _subscribe_all(chain, quantities, price)
    chain.travel(timestamp(spec.issue_date))
    chain.send(chain.asset.functions.finalize(), chain.operator)
    failed = chain.asset.functions.phase().call() == 2
    refunded = True
    if failed:
        for investor, quantity in zip(chain.investors, quantities, strict=False):
            before = chain.balance(investor)
            chain.send(chain.asset.functions.refund(), investor)
            refunded &= chain.balance(investor) - before == quantity * price
    ok = failed and refunded
    return _check(
        "refund",
        title,
        ok,
        f"Заявки на {group_digits(spec.min_quantity - 1)} ЦФА: выпуск не состоялся, средства возвращены"
        if ok
        else f"При заявках на {group_digits(spec.min_quantity - 1)} ЦФА выпуск признан состоявшимся",
    )


def run_scenarios(
    compilation: Compilation, contract: GeneratedContract, spec: IssueSpec, schedule: Schedule
) -> list[Check]:
    checks = _primary_scenario(compilation, contract, spec, schedule)
    checks.insert(-1, _funding_scenario(compilation, spec, schedule))
    checks.insert(-1, _failed_issue_scenario(compilation, spec))
    return checks
