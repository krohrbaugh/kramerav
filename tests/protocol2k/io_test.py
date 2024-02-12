import logging
import pytest
import random
import socket

from kesslerav.protocol2k.io import \
  Command, Instruction, Codec, TcpDevice, TcpEndpoint, _VALID_RANGE

from fakes import FakeSocket

class TestCommand:
  def test_is_supported_returns_true_for_known_command_id(self):
    valid_cmd = gen_valid_cmd()

    result = Command.is_supported(valid_cmd)

    assert result is True

  def test_is_supported_returns_false_for_unknown_command_id(self):
    invalid_cmd_id = gen_invalid_cmd_id()

    result = Command.is_supported(invalid_cmd_id)

    assert result is False

class TestInstruction:
  def test_name_returns_command_name_for_supported_commands(self):
    valid_cmd = gen_valid_cmd()

    result = Instruction(valid_cmd)

    assert result.name == valid_cmd.name

  def test_name_returns_unsupported_for_unsupported_commands(self):
    invalid_cmd_id = gen_invalid_cmd_id()

    result = Instruction(invalid_cmd_id)

    assert result.name == Instruction.UNSUPPORTED_COMMAND_NAME

  def test_id_returns_command_id_for_supported_commands(self):
    valid_cmd = gen_valid_cmd()

    result = Instruction(valid_cmd)

    assert result.id == valid_cmd.value

  def test_id_returns_unsupported_command_id_for_unsupported_commands(self):
    invalid_cmd_id = gen_invalid_cmd_id()

    result = Instruction(invalid_cmd_id)

    assert result.id == invalid_cmd_id

  def test_input_value_returns_value_when_valid(self):
    valid_cmd = gen_valid_cmd()
    input_value = gen_valid_io_value()

    result = Instruction(valid_cmd, input_value)

    assert result.input_value == input_value

  def test_input_value_raises_exception_when_invalid(self):
    valid_cmd = gen_valid_cmd()
    input_value = gen_invalid_io_value()

    with pytest.raises(ValueError):
      Instruction(valid_cmd, input_value)

  def test_output_value_returns_value_when_valid(self):
    valid_cmd = gen_valid_cmd()
    input_value = gen_valid_io_value()
    output_value = gen_valid_io_value()

    result = Instruction(valid_cmd, input_value, output_value)

    assert result.output_value == output_value
  
  def test_output_value_raises_exception_when_invalid(self):
    valid_cmd = gen_valid_cmd()
    input_value = gen_valid_io_value()
    output_value = gen_invalid_io_value()

    with pytest.raises(ValueError):
      Instruction(valid_cmd, input_value, output_value)

  def test_machine_id_returns_default_when_not_provided(self):
    valid_cmd = gen_valid_cmd()

    result = Instruction(valid_cmd)

    assert result.machine_id == Instruction.DEFAULT_MACHINE_ID

  def test_machine_id_returns_value_when_valid(self):
    valid_cmd = gen_valid_cmd()
    input_value = gen_valid_io_value()
    output_value = gen_valid_io_value()
    machine_id = random.randrange(1, 10)

    result = Instruction(valid_cmd, input_value, output_value, machine_id)

    assert result.machine_id == machine_id

  def test_machine_id_raises_exception_when_invalid(self):
    valid_cmd = gen_valid_cmd()
    input_value = gen_valid_io_value()
    output_value = gen_valid_io_value()
    machine_id = gen_invalid_io_value()

    with pytest.raises(ValueError):
      Instruction(valid_cmd, input_value, output_value, machine_id)

  def test_frame_returns_list_of_data(self):
    valid_cmd = gen_valid_cmd()
    input_value = gen_valid_io_value()
    output_value = gen_valid_io_value()
    machine_id = gen_valid_io_value()
    expected = [valid_cmd, input_value, output_value, machine_id]
    instruction = Instruction(*expected)

    result = instruction.frame

    assert result == expected

class TestCodec:
  def test_encode_generates_valid_bytes(self):
    expected = b'\x1f\x80\x80\xc1'
    cmd = Instruction(Command.QUERY_PANEL_LOCK)

    result = Codec.encode(cmd)

    assert result == expected

  def test_decode_hydrates_from_request_bytes(self):
    req_bytes = b'\x1f\x80\x80\xc1'
    expected = Instruction(Command.QUERY_PANEL_LOCK)

    result = Codec.decode(req_bytes)

    assert result == expected

  def test_decode_hydrates_from_response_bytes(self):
    resp_bytes = b'\x5f\x80\x80\xc1'
    expected = Instruction(Command.QUERY_PANEL_LOCK)

    result = Codec.decode(resp_bytes)

    assert result == expected

  def test_decode_encode_returns_starting_value(self):
    input = b'\x1f\x80\x80\xc1'
    cmd = Codec.decode(input)

    result = Codec.encode(cmd)

    assert result == input

  def test_encode_decode_returns_starting_value(self):
    input = Instruction(Command.QUERY_PANEL_LOCK)
    req_bytes = Codec.encode(input)

    result = Codec.decode(req_bytes)

    assert result == input

class TestTcpEndpoint:
  _host = 'localhost'

  def test_host_returns_specified_value(self):
    expected = self._host

    sut = TcpEndpoint(expected)

    assert sut.host == expected

  def test_port_returns_specified_value_when_provided(self):
    expected = gen_port()

    sut = TcpEndpoint(self._host, expected)

    assert sut.port == expected

  def test_port_returns_default_value_when_not_provided(self):
    port = None

    sut = TcpEndpoint(self._host, port)

    assert sut.port == TcpEndpoint.DEFAULT_PORT

  def test_timeout_returns_specified_value_when_provided(self):
    expected = 0.5

    sut = TcpEndpoint(self._host, gen_port(), expected)

    assert sut.timeout_sec == expected

  def test_timeout_returns_none_when_none_provided(self):
    sut = TcpEndpoint(self._host, gen_port(), None)

    assert sut.timeout_sec is None

  def test_timeout_returns_default_when_elided(self):
    sut = TcpEndpoint(self._host, gen_port())

    assert sut.timeout_sec == TcpEndpoint.DEFAULT_TIMEOUT_SEC

class TestTcpDevice:
  def test_creates_connection_using_specified_endpoint_details(self, monkeypatch: pytest.MonkeyPatch):
    expected_host = '10.0.0.1'
    expected_port = 1337
    expected_timeout = 0.101
    captured_host = False
    captured_port = False
    captured_timeout_sec = False
    fake_socket = FakeSocket()
    def capture_create_connection(host_port_tuple, timeout_sec):
      nonlocal captured_host, captured_port, captured_timeout_sec
      captured_host = host_port_tuple[0]
      captured_port = host_port_tuple[1]
      captured_timeout_sec = timeout_sec
      return fake_socket
    monkeypatch.setattr(socket, 'create_connection', capture_create_connection)
    endpoint = TcpEndpoint(expected_host, expected_port, expected_timeout)
    sut = TcpDevice(endpoint)

    sut.process(Instruction(Command.QUERY_PANEL_LOCK))

    assert captured_host == expected_host
    assert captured_port == expected_port
    assert captured_timeout_sec == expected_timeout

  def test_process_dispatches_single_instruction(self, monkeypatch: pytest.MonkeyPatch):
    instruction = Instruction(Command.QUERY_PANEL_LOCK)
    expected_bytes = Codec.encode(instruction)
    fake_socket = self.stub_socket(monkeypatch)
    sut = self.create_device()

    sut.process(instruction)

    assert fake_socket.request_bytes[0] == expected_bytes

  def test_process_dispatches_multiple_instruction(self, monkeypatch: pytest.MonkeyPatch):
    instruction1 = Instruction(Command.QUERY_PANEL_LOCK)
    expected_bytes1 = Codec.encode(instruction1)
    instruction2 = Instruction(Command.QUERY_OUTPUT_STATUS)
    expected_bytes2 = Codec.encode(instruction2)
    instructions = [instruction1, instruction2]
    fake_socket = self.stub_socket(monkeypatch)
    sut = self.create_device()

    sut.process(instructions)

    assert fake_socket.send_count == 2
    assert fake_socket.request_bytes[0] == expected_bytes1
    assert fake_socket.request_bytes[1] == expected_bytes2

  def test_process_continues_without_erroring_when_no_response_received(
        self,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch
      ):
      caplog.set_level(logging.INFO)
      instruction1 = Instruction(Command.QUERY_PANEL_LOCK)
      instruction2 = Instruction(Command.QUERY_OUTPUT_STATUS)
      instructions = [instruction1, instruction2]
      fake_socket = self.stub_socket(monkeypatch)
      fake_socket.should_timeout = True
      sut = self.create_device()

      result = sut.process(instructions)

      assert 'Timed out' in caplog.text
      assert fake_socket.send_count == 2
      assert len(result) == 0
    
  def test_process_returns_multiple_response_instructions(self, monkeypatch: pytest.MonkeyPatch):
    response_bytes = b'\x5e\x80\x80\x81\x5f\x80\x80\x81'
    instruction = Instruction(Command.QUERY_PANEL_LOCK)
    expected_results = [
      Instruction(Command.PANEL_LOCK, 0, 0, 1),
      Instruction(Command.QUERY_PANEL_LOCK, 0, 0, 1)
    ]
    fake_socket = self.stub_socket(monkeypatch)
    fake_socket.response_bytes = response_bytes
    sut = self.create_device()

    results = sut.process(instruction)

    assert results == expected_results

  def test_process_closes_connection_when_complete(self, monkeypatch: pytest.MonkeyPatch):
    instruction = Instruction(Command.QUERY_OUTPUT_STATUS)
    fake_socket = self.stub_socket(monkeypatch)
    sut = self.create_device()

    sut.process(instruction)

    assert fake_socket.was_closed

  def stub_socket(self, patch: pytest.MonkeyPatch) -> FakeSocket:
    fake_socket = FakeSocket()
    patch.setattr(socket, 'create_connection', lambda *_: fake_socket)
    return fake_socket

  def create_device(self, endpoint: TcpEndpoint = TcpEndpoint('localhost')):
    return TcpDevice(endpoint)

#
# Helpers
#
def gen_invalid_cmd_id(rand = random) -> int:
  return rand.randrange(64, 128)

def gen_valid_cmd(rand = random) -> Command:
  return random.choice(list(Command))

def gen_valid_io_value(rand = random) -> int:
  return rand.choice(_VALID_RANGE)

def gen_invalid_io_value(rand = random) -> int:
  max_valid = _VALID_RANGE.stop
  return rand.randrange(max_valid, max_valid + 100)

def gen_port(rand = random) -> int:
  return rand.randrange(49152, 65535)

