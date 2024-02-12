"""
Encapsulates Protocol 2000 communication and devices
"""
from typing import Optional

from ..media_switch import MediaSwitch as MediaSwitchProtocol
from .io import TcpDevice, TcpEndpoint
from .media_switch import MediaSwitch

def get_tcp_media_switch(
    host: str,
    port: Optional[int] = None,
    timeout_sec: Optional[float] = None,
    machine_id: Optional[int] = None
  ) -> MediaSwitchProtocol:
  endpoint = TcpEndpoint(host, port, timeout_sec)
  tcp_device = TcpDevice(endpoint)
  return MediaSwitch(tcp_device, machine_id)