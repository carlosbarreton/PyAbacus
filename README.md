# pyAbacus

pyAbacus was built to simplify the usage of Tausand Abacus family of coincidence counters, providing a library aimed to interface these devices using Python coding.

Written in Python3, pyAbacus relies on the following modules:

- pyqtgraph
- NumPy
- PyQt5
- pyserial


## Installation
`pyAbacus` can be installed using `pip` as: 
```
pip install pyAbacus
```

Or from GitHub
```
pip install git+https://github.com/Tausand-dev/PyAbacus.git
```

## For developers
### Creating a virtual environment
Run the following code to create a virtual environment called `.venv`
```
python -m venv .venv
```

#### Activate
- On Unix systems:
```
source .venv/bin/activate
```
- On Windows:
```
.venv\Scripts\activate
```

#### Deactivate
```
deactivate
```

### Installing packages
After the virtual environment has been activated, install required packages by using:
```
python -m pip install -r requirements.txt
```

### Building docs
Run 
```
make <command>
```
Where `<command>` is one of the following:
- `latexpdf`
- `html`