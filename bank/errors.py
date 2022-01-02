class BankError(Exception):
    pass


class CannotCaptureMoreThanAuthorized(BankError):
    pass


class CannotRefundMoreThanCaptured(BankError):
    pass


class InsufficientFundsError(BankError):
    def __init__(self):
        super(InsufficientFundsError, self).__init__("Insufficient funds")


class InvalidAmountError(BankError):
    pass


class AuthorizationAlreadyCapturedError(BankError):
    pass


class CaptureNotAuthorized(BankError):
    pass


class CancelationNotAuthorized(BankError):
    pass


class CannotCancelCapturedTransaction(BankError):
    pass


class AccountNotFoundError(BankError):
    def __init__(self, account: str):
        super(AccountNotFoundError, self).__init__(f"Account {account} does not exist")
