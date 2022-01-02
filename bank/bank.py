import random
from enum import Enum
from threading import Lock
from typing import Dict, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, PrivateAttr

from bank.errors import (
    AccountNotFoundError,
    AuthorizationAlreadyCapturedError,
    CancelationNotAuthorized,
    CannotCancelCapturedTransaction,
    CannotCaptureMoreThanAuthorized,
    CannotRefundMoreThanCaptured,
    CaptureNotAuthorized,
    InsufficientFundsError,
    InvalidAmountError,
)
from bank.utils import random_authorization_code, random_card_number


class Capture(BaseModel):
    amount: int


class Refund(BaseModel):
    amount: int


class Status(str, Enum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    CANCELLED = "cancelled"


class Transaction(BaseModel):
    id: UUID = uuid4()
    amount: int
    status: Status = Status.CREATED
    authorization_code: str
    _captures: List[Capture] = PrivateAttr(default_factory=list)
    _refunds: List[Refund] = PrivateAttr(default_factory=list)

    def capture(self, amount: int) -> Capture:
        if not self.is_authorized():
            raise CaptureNotAuthorized()

        captured_amount = sum(capture.amount for capture in self._captures)

        if captured_amount + amount > self.amount:
            raise CannotCaptureMoreThanAuthorized()

        capture = Capture(amount=amount)
        self._captures.append(capture)
        return capture

    def has_captures(self) -> bool:
        return len(self._captures) > 0

    def is_cancelled(self) -> bool:
        return self.status == Status.CANCELLED

    def is_authorized(self) -> bool:
        return self.status == Status.AUTHORIZED

    def cancel(self):
        if self.is_cancelled():
            return

        if not self.is_authorized():
            raise CancelationNotAuthorized()

        if self.has_captures():
            raise CannotCancelCapturedTransaction()

        self.status = Status.CANCELLED

    def refund(self, amount: int) -> Refund:
        captured_amount = sum(capture.amount for capture in self._captures)
        refunded_amount = sum(refund.amount for refund in self._refunds)

        if refunded_amount + amount > captured_amount:
            raise CannotRefundMoreThanCaptured()

        refund = Refund(amount=amount)
        self._refunds.append(refund)
        return refund


class Account:
    def __init__(self, balance: int) -> None:
        self.__lock = Lock()
        self.__balance = balance
        self.__authorized_amount = 0
        self.__transactions: Dict[UUID, Transaction] = dict()

    def __reduce_hold(self, amount: int):
        if self.__authorized_amount < amount:
            raise InsufficientFundsError()

        self.__authorized_amount -= amount

    def __authorize_amount(self, amount: int):
        if amount < 0:
            raise InvalidAmountError()

        if self.__balance >= amount:
            self.__balance -= amount
            self.__authorized_amount += amount
            return

        raise InsufficientFundsError()

    def __add_transaction(self, amount: int) -> Transaction:
        transaction = Transaction(
            amount=amount,
            status=Status.AUTHORIZED,
            authorization_code=random_authorization_code(),
        )
        self.__transactions[transaction.id] = transaction
        return transaction

    def deposit(self, amount: int):
        with self.__lock:
            if amount < 0:
                raise InvalidAmountError()

            self.__balance += amount

    def withdraw(self, amount: int):
        with self.__lock:
            if amount < 0:
                raise InvalidAmountError()

            if self.__balance < amount:
                raise InsufficientFundsError()

            self.__balance -= amount

    def balance(self) -> int:
        with self.__lock:
            return self.__balance

    def authorized_amount(self) -> int:
        with self.__lock:
            return self.__authorized_amount

    def authorize(self, amount: int) -> UUID:
        with self.__lock:
            self.__authorize_amount(amount)
            return self.__add_transaction(amount).id

    def capture(self, transaction_id: UUID, amount: int):
        with self.__lock:
            authorization = self.__transactions[transaction_id]
            authorization.capture(amount)
            self.__reduce_hold(amount)

    def cancel(self, transaction_id: UUID) -> None:
        with self.__lock:
            authorization = self.__transactions[transaction_id]
            authorization.cancel()
            self.__balance += authorization.amount
            self.__authorized_amount -= authorization.amount

    def refund(self, transaction_id: UUID, amount: int) -> None:
        with self.__lock:
            authorization = self.__transactions[transaction_id]
            authorization.refund(amount)
            self.__balance += amount


class Bank:
    def __init__(self) -> None:
        self.__accounts: Dict[str, Account] = dict()

    def __set_account(self, name: str, account: Account):
        self.__accounts[name] = account

    def __get_account(self, name: str) -> Account:
        try:
            return self.__accounts[name]
        except KeyError:
            raise AccountNotFoundError(name)

    def open_account(self, initial_balance: int = 0) -> str:
        account_name = random_card_number()
        self.__set_account(account_name, Account(initial_balance))
        return account_name

    def deposit(self, account_name: str, amount: int):
        account = self.__get_account(account_name)
        account.deposit(amount)

    def withdraw(self, account_name: str, amount: int):
        account = self.__get_account(account_name)
        account.withdraw(amount)

    def balance(self, account_name: str) -> int:
        account = self.__get_account(account_name)
        return account.balance()

    def authorized_amount(self, account_name: str) -> int:
        account = self.__get_account(account_name)
        return account.authorized_amount()

    def authorize(self, account_name: str, amount: int) -> UUID:
        account = self.__get_account(account_name)
        return account.authorize(amount)

    def cancel(self, account_name: str, transaction_id: UUID):
        account = self.__get_account(account_name)
        account.cancel(transaction_id)

    def capture(self, account_name: str, transaction_id: UUID, amount: int):
        account = self.__get_account(account_name)
        account.capture(transaction_id, amount)

    def refund(self, account_name: str, transaction_id: UUID, amount: int):
        account = self.__get_account(account_name)
        account.refund(transaction_id, amount)
