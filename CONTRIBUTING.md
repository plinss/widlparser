Contributing to widlparser
==========================

All contributions are welcome!


Testing
-------

To ensure that there are no unexpected changes, compare the output of `test.py`:

       ./test.py > test-actual.txt
       diff test-expected.txt test-actual.txt

If all changes are expected, include them in your pull request:

       mv test-actual.txt test-expected.txt
       git add test-expected.txt
