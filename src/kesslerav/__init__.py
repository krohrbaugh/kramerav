"""Kramer A/V Protcol 2000 control library"""
from typing import Optional

from .constants import PROTOCOL_2K, SCHEME_TCP
from .url_parser import parse_url
from .media_switch import MediaSwitch

from .protocol2k import get_tcp_media_switch

def get_media_switch(
    url: str,
    timeout_sec: Optional[float] = None,
    machine_id: Optional[int] = None
  ) -> list[MediaSwitch]:
  """
  Create media switch representation whose state can be accessed via the specified
  URL.

  Currently supported:
    + Schemes:
      + TCP (identifier: tcp)
    + Protocols:
      + Protocol 2000 (identifier: protocol2k)

  Defaults:
    + Default scheme: TCP (identifier: tcp)
    + Default TCP port: 5000
    + Default protocol: Protocol 2000 (identifier: protocol2k)

  URL format:
    The URL takes the form of `<scheme>://<host>:<port>#<protocol>` with all
    but the host being optional.

    Examples:
      + 10.0.0.1 ->
          Scheme: tcp, Host: 10.0.0.1, Port: 5000, Protocol: protocol2k
      + localhost:1337 ->
          Scheme: tcp, Host: localhost, Port: 1337, Protocol: protocol2k
      + localhost:1337#protocol2000 ->
          Scheme: tcp, Host: localhost, Port: 1337, Protocol: protocol2k
      + tcp://10.0.0.1 ->
          Scheme: tcp, Host: 10.0.0.1, Port: 5000, Protocol: protocol2k
      + tcp://switch.local:8080 ->
          Scheme: tcp, Host: switch.local, Port: 8080, Protocol: protocol2k
      + tcp://localhost:8080#protocol2k
          Scheme: tcp, Host: localhost, Port: 8080, Protocol: protocol2k

  Args:
    url (str): The URL at which the device state can be accessed.
    timeout_sec (Optional[float]): Timeout, in seconds, to use when communicating
      with the device. Default: None, which allows the underlying protocol driver
      to determine.
    machine_id (Optional[int]): Specifies the machine ID of the target device.
      This is only applicable with serial communications. Default: None, which
      allows the underlying protocol driver to determine.

  Returns:
    list[MediaSwitch]: Representation of the media switch device, including methods for
      controlling it (e.g., selecting sources.). Each output of a matrix-type device is a MediaSwitch instance. Switches will have only one instance.
  """
  endpoint = parse_url(url)
  if endpoint.protocol == PROTOCOL_2K and endpoint.scheme == SCHEME_TCP:
    return get_tcp_media_switch(
      host = endpoint.host,
      port = endpoint.port,
      timeout_sec = timeout_sec,
      machine_id = machine_id
    )
  else:
    raise ValueError(f'Unsupported url specified: {url}')
