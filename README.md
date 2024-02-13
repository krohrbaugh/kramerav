# kessler-av

Python library for controlling a [Kramer][kramer] media switch that uses
[Protocol 2000][p2000] over a TCP connection.

It's primarily intended for use as a device driver for a [Home Assistant][ha]
integration.

## USAGE

```py
from kesslerav import get_media_switch

device_url = '10.0.0.1'
media_switch = get_media_switch(device_url)

media_switch.select_source(3) # Change to input 3
media_switch.lock() # Lock front panel
media_switch.unlock() # Unlock front panel
media_switch.update() # Refreshes device state
```

See `src/kesslerav/media_switch.py` for full `MediaSwitch` capabilities.

### Device URL format

The URL takes the form of `<scheme>://<host>:<port>#<protocol>` with all
but `host` being optional.

Default scheme is `tcp`, with a default port of `5000`.

Default protocol is Protocol 2000 (identifier: `protocol2k`.)

Examples:

+ `10.0.0.1` ->
  Scheme: `tcp`, Host: `10.0.0.1`, Port: `5000`, Protocol: `protocol2k`
+ `localhost:1337` ->
  Scheme: `tcp`, Host: `localhost`, Port: `1337`, Protocol: `protocol2k`
+ `localhost:1337#protocol2000` ->
  Scheme: `tcp`, Host: `localhost`, Port: `1337`, Protocol: `protocol2k`
+ `tcp://10.0.0.1` ->
  Scheme: `tcp`, Host: `10.0.0.1`, Port: `5000`, Protocol: `protocol2k`
+ `tcp://switch.local:8080` ->
  Scheme: `tcp`, Host: `switch.local`, Port: `8080`, Protocol: `protocol2k`
+ `tcp://localhost:8080#protocol2k`
  Scheme: `tcp`, Host: `localhost`, Port: `8080`, Protocol: `protocol2k`

## Limitations

The library was tested and developed using a Kramer [VS-161HDMI switch][vs161h],
but _should_ work for any Kramer switch using Protocol 2000.

It does _not_ currently support:

+ _Matrix_ switch operations, since I don't have a device to test with
+ UDP communication, since I don't have a device to test with
+ Serial communication, since TCP is the more likely control mechanism for home
automation purposes

The library has extension points for adding the support above should an
opportunity or need to do so arise.

## Development workflow

### Python environment

Workflow scripts assume a working Python environment, including `pip`.

Remember to be kind to yourself and use a virtual environment.

```sh
python3 -m venv env
env/bin/activate
```

### Setup

Install development and runtime dependencies. This also installs the library as an
editable path, so that it can be loaded in the REPL and `pytest`.

```sh
script/setup
```

### Tests

Run unit tests:

```sh
script/test
```

Tests can also be continuously run while developing with:

```sh
ptw .
```

### Build

To build distributables:

```sh
script/build
```

Build artifacts will be placed in the `dist` directly.

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

### Why `kessler-av`?

In [Seinfeld][sf], the character [Cosmo Kramer][ck] was based on comedian [Kenny
Kramer][kr2]. In the shows pilot, the producers hadn't gotten permission to use
Kenny Kramer's name, so the character was called Kessler instead.

This library controls [Kramer A/V's][kramer] media switches, but doesn't have
permission to use _their_ trademarked name. It seemed fitting, therefore, to
name it `kessler-av`.

[ck]: https://en.wikipedia.org/wiki/Cosmo_Kramer
[ha]: https://www.home-assistant.io/
[kr2]: https://en.wikipedia.org/wiki/Kenny_Kramer
[kramer]: https://www.kramerav.com/
[p2000]: https://cdn.kramerav.com/web/downloads/tech-papers/protocol_2000_rev0_51.pdf
[sf]: https://en.wikipedia.org/wiki/Seinfeld
[vs161h]: https://www1.kramerav.com/au/product/VS-161H
