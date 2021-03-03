# PySA2
PySA2  is the Python Source-code Analyzer for Python 2.7 that exploits Python AST.

If you want to mention PySA2 in a research paper, please cite the following references:

```bibtex
@inproceedings{cotroneo2019analyzing,
  title={Analyzing the context of bug-fixing changes in the openstack cloud computing platform},
  author={Cotroneo, Domenico and De Simone, Luigi and Iannillo, Antonio Ken and Natella, Roberto and Rosiello, Stefano and Bidokhti, Nematollah},
  booktitle={2019 IEEE 30th International Symposium on Software Reliability Engineering (ISSRE)},
  pages={334--345},
  year={2019},
  organization={IEEE}
}
```

# Requirements

PySA2 works with python 2.7, for both interpreter and target code.

Install the requirements through:
```shell
pip install -r requirements.txt
```

# Tests

In order to run the tests:
```shell
cd tests
python run_test.py
```
