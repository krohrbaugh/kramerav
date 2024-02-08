# kramerav - Kramer Protcol 2000 video switcher library

Python library for controlling a Kramer HDMI switch that uses Protocol 2000.

## Development workflow

### Python environment

Workflow scripts assume a working Python environment, including `pip`.

Remember to be kind to yourself and use a virtual environment.

```sh
python3 -m venv env
env/bin/activate
```

### Setup

Install development and runtime dependencies.

```sh
script/setup
```

### Publishing

Build the distribution.

```sh
script/build
```

Publish the library to TestPyPI.

```sh
script/publish_test
```

Publish the library to PyPI.

```sh
script/publish
```
