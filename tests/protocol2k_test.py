import pytest
import random
from kramerav.protocol2k import Codec, Command, Instruction, _VALID_RANGE, _VALUE_MAX

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
    assert result.name == Instruction.unsupported_command_name

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
    assert result.machine_id == Instruction.default_machine_id

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


def gen_invalid_cmd_id(rand = random) -> int:
  return rand.randrange(64, 128)

def gen_valid_cmd(rand = random) -> Command:
  return random.choice(list(Command))

def gen_valid_io_value(rand = random) -> int:
  return rand.choice(_VALID_RANGE)

def gen_invalid_io_value(rand = random) -> int:
  return rand.randrange(_VALUE_MAX, _VALUE_MAX + 100)
