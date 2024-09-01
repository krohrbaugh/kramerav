import itertools
import socket
import struct
import time

from ..constants import LOGGER
from enum import IntEnum, unique
from typing import Optional


@unique
class Command(IntEnum):
  """
  Enumerates the supported Protocol 2000 commands
  """
  SWITCH_VIDEO = 1
  SWITCH_AUDIO = 2
  RECALL_VIDEO_STATUS = 4
  ERROR = 16
  PANEL_LOCK = 30
  QUERY_VIDEO_OUTPUT_STATUS = 5
  QUERY_AUDIO_OUTPUT_STATUS = 6
  QUERY_PANEL_LOCK = 31
  IDENTIFY_MACHINE = 61
  DEFINE_MACHINE = 62

  @classmethod
  def is_supported(cls, cmd_id: int) -> bool:
    return cmd_id in iter(Command)


# Validation rules: limit I/O values to one byte
_VALUE_MIN = 0
_VALUE_MAX = 128 # Only 7 bits available for data transport
_VALID_RANGE: range = range(_VALUE_MIN, _VALUE_MAX)


def _validated_value(
    maybe_value: Optional[int],
     default_value: int = 0) -> int:
  if maybe_value is None:
    return default_value
  if maybe_value not in _VALID_RANGE:
    raise ValueError(
      f'Valid values are between {_VALUE_MIN} and {_VALUE_MAX - 1}, '
      f'inclusive. Received: {maybe_value}'
    )
  else:
    return maybe_value

class Instruction:
  """
  Encapsulates a fully-formed Protocol 2000 instruction
  """

  # Defaults to the override value, meaning ALL machines receiving the instruction
  # will respond, regardless of machine ID setting.
  DEFAULT_MACHINE_ID: int = 0b01000001

  # Default name for unsupported/unrecognized commands
  UNSUPPORTED_COMMAND_NAME: str = "UNSUPPORTED"

  # Protocol 2000 uses 4-byte instructions
  SIZE_BYTES: int = 4
  FORMAT: str = '!I' # 4-bytes

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
      Instruction.DEFAULT_MACHINE_ID
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
      return Instruction.UNSUPPORTED_COMMAND_NAME

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

  def __str__(self) -> str:
    return (
      f'<Instruction id: {self.id} name: {self.name} input: {self.input_value} '
      f'output: {self.output_value} machine_id: {self.machine_id}>'
    )

  def __repr__(self) -> str:
    return (
      f'Instruction<{self.name}>({self.id}, {self.input_value}, '
      f'{self.output_value}, {self.machine_id})'
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

class TcpEndpoint:
  """
  Protocol 2000 TCP endpoint location details
  """
  DEFAULT_PORT: int = 5000
  DEFAULT_TIMEOUT_SEC: float = 0.250

  def __init__(
      self,
      host: str,
      port: Optional[int] = None,
      timeout_sec: Optional[float] = DEFAULT_TIMEOUT_SEC
    ):
    self._host = host
    if port is None:
      self._port = TcpEndpoint.DEFAULT_PORT
    else:
      self._port = port
    self._timeout_sec = timeout_sec

  @property
  def host(self) -> str:
    return self._host

  @property
  def port(self) -> int:
    return self._port

  @property
  def timeout_sec(self) -> Optional[float]:
    return self._timeout_sec

class TcpDevice:
  """
  Manages TCP I/O for a specific Protocol 2000-based device
  """
  # Maximum number of response instructions to read
  PAGE_SIZE: int = 32
  # Size of the buffer used to read responses
  BUFFER_SIZE_BYTES: int = Instruction.SIZE_BYTES * PAGE_SIZE

  def __init__(
      self,
      endpoint: TcpEndpoint,
    ):
    self._endpoint = endpoint

  def process(self, instructions: list[Instruction]
              | Instruction) -> list[Instruction]:
    try:
      _ = iter(instructions)
    except TypeError:
      # Single instruction provided; wrap it.
      instructions = [instructions]
    results = []

    conn = self._create_connection()
    try:
      for instruction in instructions:
        result = self._execute_instruction(instruction, conn)
        results.append(result)
    except Exception as ex:
      LOGGER.error('Failed communicating with device: %s', ex)
    finally:
      conn.close()

    # Results is a list of lists, so flatten before returning
    flat_results = list(itertools.chain.from_iterable(results))
    return flat_results

  def _create_connection(self) -> socket.socket:
    return socket.create_connection(
      (self._endpoint.host, self._endpoint.port),
      self._endpoint.timeout_sec
    )

  def _execute_instruction(
      self,
      instruction: Instruction,
      conn: socket.socket
    ) -> list[Instruction]:
    req_bytes= Codec.encode(instruction)
    conn.send(req_bytes)
    # Device can return multiple instructions when its physical controls are
    # used. To capture them all (to reconstruct device state) we read using a
    # buffer that can hold multiple instructions and then return them all in
    # chronological event order.
    result: list[Instruction]= []
    try:
      while len(result) < 1:
        time.sleep(0.5) # Slow down to prevent 'port already in use' errors when interacting with serial over TCP TODO configurable, default off
        data= conn.recv(TcpDevice.BUFFER_SIZE_BYTES)
        responses= struct.iter_unpack(Instruction.FORMAT, data)
        for response in responses:
          resp_bytes= response[0].to_bytes(Instruction.SIZE_BYTES)
          instruction= Codec.decode(resp_bytes)
          result.append(instruction)
    except TimeoutError:
      LOGGER.info(
        'Timed out waiting for response. Ignoring, since another thread may '
        'have processed the response already.'
      )

    return result
