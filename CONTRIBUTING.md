Contributing to widlparser
==========================

All contributions are welcome!

Linting
-------

Please install all the dev requirements, e.g.:

    pip install -e '.[dev]'

and ensure that `flake8 widlparser` and `mypy widlparser` do not return any errors.


Testing
-------

To ensure that there are no unexpected changes, compare the output of `test.py`:

    ./test.py | diff -u test-expected.txt -

If all changes are expected, include them in your pull request:

    ./test.py > test-expected.txt
    git add test-expected.txt