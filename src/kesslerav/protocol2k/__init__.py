"""
Encapsulates Protocol 2000 communication and devices
"""
from typing import Optional

from ..media_switch import MediaSwitch as MediaSwitchProtocol
from .io import TcpDevice, TcpEndpoint, Instruction, Command
from .media_switch import MediaSwitch


def get_switch_or_matrix(connection_device, machine_id):
    # Need to know output count early when setting up matrix, so get it here
    output_count = connection_device.process(Instruction(Command.DEFINE_MACHINE, 2, 1, machine_id))[0].output_value
    if output_count > 1:
        return [MediaSwitch(connection_device, machine_id, output_count) for output_count in range(output_count)]
    else:
        return [MediaSwitch(connection_device, machine_id)]

def get_tcp_media_switch(
    host: str,
    port: Optional[int] = None,
    timeout_sec: Optional[float] = None,
    machine_id: Optional[int] = None
  ) -> MediaSwitchProtocol:
  if timeout_sec is None:
    # Let `TcpEndpoint` manage timeout
    endpoint = TcpEndpoint(host, port)
  else:
    endpoint = TcpEndpoint(host, port, timeout_sec)
  tcp_device = TcpDevice(endpoint)
  return get_switch_or_matrix(tcp_device, machine_id)
