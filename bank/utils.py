import random
from typing import Any, Iterable, Optional


def concat(seq: Iterable[Any]) -> str:
    return "".join(str(i) for i in seq)


def random_card_number(length: int = 15, card_bin: Optional[int] = None) -> str:
    def luhn_number(i: int, n: int) -> int:
        # offset if length is odd to correctly calculate the odd position from right to left
        k = length % 2
        n *= 1 if (i + k) % 2 == 0 else 2
        return n if n <= 9 else n - 9

    if card_bin is not None:
        number = [int(n) for n in str(card_bin)]
        number.extend(random.choices(range(10), k=length - len(number)))
    else:
        number = random.choices(range(10), k=length)

    checksum = sum(luhn_number(i, n) for i, n in enumerate(number))

    checksum = 0 if checksum == 0 else 10 - checksum % 10
    number.append(checksum)
    return concat(number)


def random_authorization_code() -> str:
    return concat(random.choices(range(10), k=6))
