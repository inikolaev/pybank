# Bank

This is a toy bank implementation that supports basic operations:

* Open an account
* Deposit amoount to the account
* Withdraw amount from the account
* Authorize card transaction
* Cancel authorized card transaction
* Capture authorized card transaction
* Issue refunds for th authorized card transaction

## Development

### Managing dependencies

This project uses Poetry to manage dependencies. Use the following command to install it:

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

To create virtual environment and install dependencies run

```bash
poetry install
```

### Running tests

```bash
poetry run pytest
```