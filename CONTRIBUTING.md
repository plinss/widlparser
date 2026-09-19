Contributing to widlparser
==========================

All contributions are welcome, as long as no LLM products are used in the process.
The owner of this repository considers the usage of LLMs to be deeply unethical
for too many reasons to list here. The only winning move is not to play.


Linting
-------

Please install all the dev requirements, e.g.:

    pip install -e '.[dev]'

and ensure that `flake8 widlparser` and `pyright widlparser` do not return any errors.


Testing
-------

To ensure that there are no unexpected changes, compare the output of `test.py`:

    ./test.py | diff -u test-expected.txt -

If all changes are expected, include them in your pull request:

    ./test.py > test-expected.txt
    git add test-expected.txt