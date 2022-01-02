import pytest

from bank.bank import Bank
from bank.errors import BankError, InsufficientFundsError, InvalidAmountError


class TestBank:
    def setup_method(self):
        self.bank = Bank()
        self.account_with_funds = self.bank.open_account(1000)
        self.account_with_out_funds = self.bank.open_account(0)

    def test_deposit(self):
        self.bank.deposit(self.account_with_funds, 100)

        assert self.bank.balance(self.account_with_funds) == 1100
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_deposit_negative_amount(self):
        with pytest.raises(InvalidAmountError):
            self.bank.deposit(self.account_with_funds, -100)

        assert self.bank.balance(self.account_with_funds) == 1000
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_withdraw_everything(self):
        self.bank.withdraw(self.account_with_funds, 1000)

        assert self.bank.balance(self.account_with_funds) == 0
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_withdraw_too_much(self):
        with pytest.raises(InsufficientFundsError):
            self.bank.withdraw(self.account_with_funds, 1001)

        assert self.bank.balance(self.account_with_funds) == 1000
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_withdraw_negative_amount(self):
        with pytest.raises(InvalidAmountError):
            self.bank.withdraw(self.account_with_funds, -100)

        assert self.bank.balance(self.account_with_funds) == 1000
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_authorization(self):
        self.bank.authorize(self.account_with_funds, 100)

        assert self.bank.balance(self.account_with_funds) == 900
        assert self.bank.authorized_amount(self.account_with_funds) == 100

    def test_cancellation(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)
        self.bank.cancel(self.account_with_funds, authorization_code)

        assert self.bank.balance(self.account_with_funds) == 1000
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_single_full_refund(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)
        self.bank.capture(self.account_with_funds, authorization_code, 100)
        self.bank.refund(self.account_with_funds, authorization_code, 100)

        assert self.bank.balance(self.account_with_funds) == 1000
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_multiple_full_refund(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)
        self.bank.capture(self.account_with_funds, authorization_code, 100)
        self.bank.refund(self.account_with_funds, authorization_code, 50)
        self.bank.refund(self.account_with_funds, authorization_code, 50)

        assert self.bank.balance(self.account_with_funds) == 1000
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_partial_refund(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)
        self.bank.capture(self.account_with_funds, authorization_code, 100)
        self.bank.refund(self.account_with_funds, authorization_code, 50)

        assert self.bank.balance(self.account_with_funds) == 950
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_cannot_refund_more_than_captured(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)
        self.bank.capture(self.account_with_funds, authorization_code, 100)
        self.bank.refund(self.account_with_funds, authorization_code, 50)
        self.bank.refund(self.account_with_funds, authorization_code, 50)

        with pytest.raises(BankError):
            self.bank.refund(self.account_with_funds, authorization_code, 50)

        assert self.bank.balance(self.account_with_funds) == 1000
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_multiple_captures(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)
        self.bank.capture(self.account_with_funds, authorization_code, 60)
        self.bank.capture(self.account_with_funds, authorization_code, 40)

        assert self.bank.balance(self.account_with_funds) == 900
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_cannot_capture_more_than_authorized(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)

        with pytest.raises(BankError):
            self.bank.capture(self.account_with_funds, authorization_code, 110)

        assert self.bank.balance(self.account_with_funds) == 900
        assert self.bank.authorized_amount(self.account_with_funds) == 100

    def test_cannot_cancel_captured_transaction(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)
        self.bank.capture(self.account_with_funds, authorization_code, 100)

        with pytest.raises(BankError):
            self.bank.cancel(self.account_with_funds, authorization_code)

        assert self.bank.balance(self.account_with_funds) == 900
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_cannot_refund_non_captured_transaction(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)

        with pytest.raises(BankError):
            self.bank.refund(self.account_with_funds, authorization_code, 100)

        assert self.bank.balance(self.account_with_funds) == 900
        assert self.bank.authorized_amount(self.account_with_funds) == 100

    def test_cannot_refund_cancelled_transaction(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)
        self.bank.cancel(self.account_with_funds, authorization_code)

        with pytest.raises(BankError):
            self.bank.refund(self.account_with_funds, authorization_code, 100)

        assert self.bank.balance(self.account_with_funds) == 1000
        assert self.bank.authorized_amount(self.account_with_funds) == 0

    def test_cannot_capture_cancelled_transaction(self):
        authorization_code = self.bank.authorize(self.account_with_funds, 100)
        self.bank.cancel(self.account_with_funds, authorization_code)

        with pytest.raises(BankError):
            self.bank.capture(self.account_with_funds, authorization_code, 100)

        assert self.bank.balance(self.account_with_funds) == 1000
        assert self.bank.authorized_amount(self.account_with_funds) == 0
