from abc import ABC, abstractmethod
from typing import Optional

# TODO:
# + Write some tests that round-trip from request command to bytes and bytes to response command
# + Add fallback for unsupported commands, instead of raising ValueError
# + (Maybe) Add failback for decoding _request_ commands, instead of raising ValueError (i.e., don't decode cmd_id)
# + Think about how to structure this package; the `commands` sub-module may not make sense
#   HOWEVER, it might make more sense to keep going as-is and build the communication layer,
#   and see how it plugs into this module first. Can always move things around a bit.
# + Start working on the actual TCP connection code!

# Supported commands
_CMD_QUERY_PANEL_LOCK: tuple[str, int] = ("QUERY_PANEL_LOCK", 31)

# Used for creating commands from code (where a command name is more descriptive)
_REQUEST_MAP: dict[str, int] = dict([
  _CMD_QUERY_PANEL_LOCK,
])
# Used for creating commands from device responses (where a command ID is known)
_RESPONSE_MAP: dict[int, str] = dict(
  (cmd_id, cmd_name) for cmd_name, cmd_id in _REQUEST_MAP.items()
)

# Validation rules: limit I/O values to one byte
_VALUE_MIN = 0
_VALUE_MAX = 128 # Only 7 bits available for data transport
_VALID_RANGE: range = range(_VALUE_MIN, _VALUE_MAX)

# Machine ID defaults to the override value, meaning ALL machines receiving the
# message will respond, regardless of machine ID setting.
_DEFAULT_MACHINE_ID: int = 0b01000001

class Command:
  def __init__(
    self,
    name_or_id: str | int,
    input_value: Optional[int] = None,
    output_value: Optional[int] = None,
    maybe_machine_id: Optional[int] = None
  ):
    if name_or_id in _REQUEST_MAP:
      self._name = name_or_id
      self._id = _REQUEST_MAP[name_or_id]
    elif name_or_id in _RESPONSE_MAP:
      self._name = _RESPONSE_MAP[name_or_id]
      self._id = name_or_id
    else:
      raise ValueError(f'Unsupported command: {name_or_id}')

    self._input_value = _validated_value(input_value)
    self._output_value = _validated_value(output_value)
    self._machine_id = _validated_value(maybe_machine_id, _DEFAULT_MACHINE_ID)

  @property
  def id(self) -> int:
    return self._id

  @property
  def name(self) -> str:
    return self._name

  @property
  def input_value(self) -> int:
    return self._input_value

  @property
  def output_value(self) -> int:
    return self._output_value

  @property
  def machine_id(self) -> int:
    return self._machine_id

  @property
  def frame(self) -> list[int]:
    return [
      self.id,
      self.input_value,
      self.output_value,
      self.machine_id
    ]

  def __str__(self) -> str:
    return (
      f'<Command id: {self.id} name: {self.name} input: {self.input_value} '
      f'output: {self.output_value} machine_id: {self.machine_id}>'
    )

  def __repr__(self) -> str:
    return (
      f'Command(\'{self.name}\', {self.input_value}, {self.output_value}, {self.machine_id})'
    )
  
def _validated_value(maybe_value: Optional[int], default_value: int = 0) -> int:
  if maybe_value is None:
    return default_value
  if maybe_value not in _VALID_RANGE:
    raise ValueError(
      f'Valid values are between {_VALUE_MIN} and {_VALUE_MAX - 1}, '
      f'inclusive. Received: {maybe_value}'
    )
  else:
    return maybe_value

class Codec:
  @classmethod
  def encode(cls, cmd: Command) -> list[bytes]:
    msg = cls._encode_message(cmd)
    data = bytes(msg)
    return data
  
  @classmethod
  def decode(cls, data: bytes) -> Command:
    frame = cls._decode_message(data)
    cmd = Command(*frame)
    return cmd

  @classmethod
  def _encode_message(cls, cmd: Command) -> list[int]:
    cmd_id, *values = cmd.frame
    encoded_values = list(map(cls._encode_value, values))
    return [cmd_id] + encoded_values
  
  @classmethod
  def _decode_message(cls, data: bytes) -> list[int]:
    encoded_cmd_id, *encoded_values = [byte for byte in data]
    cmd_id = cls._decode_command_id(encoded_cmd_id)
    values = list(map(cls._decode_value, encoded_values))
    return [cmd_id] + values 

  # Per protocol, the first bit for all I/O values must be 1
  @classmethod
  def _encode_value(cls, value: int) -> int:
    return 0b10000000 | value

  # Values must have first bit set to 1, so flipping it back yields the original
  # value.
  @classmethod
  def _decode_value(cls, value: int) -> int:
    return value ^ 0b10000000

  # Response command ID is the request with the second bit set to 1. To decode,
  # flip it back to determine corresponding request command ID.
  @classmethod
  def _decode_command_id(cls, command_id: int) -> int:
    return command_id ^ 0b01000000
