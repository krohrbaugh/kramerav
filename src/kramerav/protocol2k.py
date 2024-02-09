from enum import IntEnum, unique
from typing import Optional

"""
Encapsulates the supported Protocol 2000 instruction set.
"""

@unique
class Command(IntEnum):
  """
  Enumerates the supported Protocol 2000 commands
  """
  QUERY_PANEL_LOCK = 31

  @classmethod
  def is_supported(cls, cmd_id: int) -> bool:
    return cmd_id in iter(Command)

class Instruction:
  """
  Encapsulates a fully-formed Protocol 2000 instruction
  """

  def __init__(
    self,
    cmd: int,
    input_value: Optional[int] = None,
    output_value: Optional[int] = None,
    maybe_machine_id: Optional[int] = None
  ):
    if Command.is_supported(cmd):
      self._command = Command(cmd)
      self._unsupported_command_id = None
    else:
      self._command = None
      self._unsupported_command_id = cmd

    self._input_value = _validated_value(input_value)
    self._output_value = _validated_value(output_value)
    self._machine_id = _validated_value(
      maybe_machine_id,
      Instruction.default_machine_id
    )
    
  @property
  def id(self) -> int:
    if self._command is not None:
      return self._command.value
    else:
      return self._unsupported_command_id

  @property
  def name(self) -> str:
    if self._command is not None:
      return self._command.name
    else:
      return Instruction.unsupported_command_name

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
  def is_supported(self) -> bool:
    return self._command is not None

  @property
  def frame(self) -> list[int]:
    return [
      self.id,
      self.input_value,
      self.output_value,
      self.machine_id
    ]

  # Defaults to the override value, meaning ALL machines receiving the instruction
  # will respond, regardless of machine ID setting.
  default_machine_id: int = 0b01000001

  # Default name for unsupported/unrecognized commands
  unsupported_command_name: str = "UNSUPPORTED"

  def __str__(self) -> str:
    return (
      f'<Instruction id: {self.id} name: {self.name} input: {self.input_value} '
      f'output: {self.output_value} machine_id: {self.machine_id}>'
    )

  def __repr__(self) -> str:
    return (
      f'Instruction<{self.name}>({self.id}, {self.input_value}, {self.output_value}, {self.machine_id})'
    )

  def __eq__(self, other):
    if not isinstance(other, Instruction):
      return NotImplemented
    return self.frame == other.frame

class Codec:
  """
  Bidirectionally converts between Instruction and bytes
  """

  @classmethod
  def encode(cls, instruction: Instruction) -> bytes:
    msg = cls._encode_message(instruction)
    data = bytes(msg)
    return data
  
  @classmethod
  def decode(cls, data: bytes) -> Instruction:
    frame = cls._decode_message(data)
    cmd = Instruction(*frame)
    return cmd

  @classmethod
  def _encode_message(cls, instruction: Instruction) -> list[int]:
    cmd_id, *values = instruction.frame
    encoded_values = list(map(cls._encode_value, values))
    return [cmd_id] + encoded_values
  
  @classmethod
  def _decode_message(cls, data: bytes) -> list[int]:
    cmd_id, *encoded_values = [byte for byte in data]
    if not Command.is_supported(cmd_id):
      # Command ID is likely a response-encoded ID; decode it
      cmd_id = cls._decode_command_id(cmd_id)
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

# Validation rules: limit I/O values to one byte
_VALUE_MIN = 0
_VALUE_MAX = 128 # Only 7 bits available for data transport
_VALID_RANGE: range = range(_VALUE_MIN, _VALUE_MAX)
  
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


