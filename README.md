# t9s
k9s inspired TUI for Tanzu Application Platform.

## Install t9s
### Prerequisites
- Install the latest Python 3.x.x from [python.org](https://www.python.org/downloads/)

Recommended way to install t9s is by using [pipx](https://pypa.github.io/pipx/#install-pipx).
You can `brew` install `pipx` as follows:

```bash
brew install pipx
pipx ensurepath
```

To Install latest:
```
pipx install git+https://github.com/atmandhol/t9s.git
```

To Install a specific version
```
pipx install git+https://github.com/atmandhol/t9s.git@version
```

- Run `t9s` on your command line to confirm if its installed

## Setup for Local build

* Install `poetry` on the system level using 
```
pip3 install poetry
```
* Create a virtualenv `t9s` using virtualenvwrapper and run install
```
mkvirtualenv t9s -p python3
poetry install
```

### Build
Run the following poetry command
```bash
$ poetry build
```
This will generate a dist folder with a whl file and a tar.gz file.
