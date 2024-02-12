from kesslerav.protocol2k.io import Instruction

#
# Fakes
#
class FakeSocket:
  FAKE_INSTRUCTION_BYTES = b'\x50\x80\x80\x81'

  def __init__(self):
    self.request_bytes: list[bytes] = []
    self.response_bytes: bytes = FakeSocket.FAKE_INSTRUCTION_BYTES
    self.response_buffer_size = 0
    self.response_index = 0

    self.should_timeout = False

    self.send_count = 0
    self.recv_count = 0
    self.close_count= 0
    self.was_closed = False

  def send(self, data: bytes) -> None:
    self.send_count += 1
    self.request_bytes.append(data)

  def recv(self, bufsize: int) -> bytes:
    self.recv_count += 1
    self.response_buffer_size = bufsize
    if self.should_timeout:
      raise TimeoutError
    else:
      return self.response_bytes

  def close(self) -> None:
    self.close_count += 1
    self.was_closed = True

class FakeDevice:
  def __init__(self):
    self.processed_instructions = []
    self.response_instructions = []

    self.process_count = 0

  def process(self, instructions: list[Instruction] | Instruction) -> list[Instruction]:
    try:
      _ = iter(instructions)
    except TypeError:
      instructions = [instructions]
    self.process_count += 1
    self.processed_instructions.extend(instructions)
    return self.response_instructions

  def clear_processed_instructions(self):
    self.processed_instructions = []

  def clear_response_instructions(self):
    self.response_instructions = []

  def clear_instructions(self):
    self.clear_processed_instructions()
    self.clear_response_instructions()