from typing import Optional

from ..constants import LOGGER
from ..media_switch import MediaSwitch as MediaSwitchProtocol
from .io import Command, Instruction, TcpDevice

class MediaSwitch(MediaSwitchProtocol):
  def __init__(self, device: TcpDevice, machine_id: Optional[int] = None):
    self._device = device 
    self._machine_id = machine_id
    self._is_locked = False
    self._selected_source = 0
    self._input_count = 0
    self._output_count = 0
    self.update()

  def select_source(self, input: int) -> None:
    """
    Select the specified video input
    """
    normalized_input = input
    if normalized_input < 0:
      normalized_input = 0
    elif normalized_input > self._input_count:
      normalized_input = self._input_count

    instruction = Instruction(Command.SWITCH_VIDEO, normalized_input, None, self._machine_id)
    self._selected_source = normalized_input
    self._process(instruction)

  def lock(self):
    """
    Lock panel
    """
    instruction = Instruction(Command.PANEL_LOCK, 1, None, self._machine_id)
    self._is_locked = True
    self._process(instruction)

  def unlock(self):
    """
    Unlock panel
    """
    instruction = Instruction(Command.PANEL_LOCK, 0, None, self._machine_id)
    self._is_locked = False
    self._process(instruction)
  
  def update(self) -> None:
    self._process(self._update_instructions())

  @property
  def selected_source(self) -> int:
    """
    Returns the input number of the selected source
    """
    return self._selected_source

  @property
  def input_count(self) -> int:
    """
    The number of inputs the switch has
    """
    return self._input_count

  @property
  def output_count(self) -> int:
    """
    The number of outputs the switch has
    """
    return self._output_count

  @property
  def is_locked(self) -> bool:
    """
    Returns `true` when panel is locked, `false` otherwise.
    """
    return self._is_locked

  @property
  def machine_id(self) -> int | None :
    return self._machine_id

  def _process(self, instructions: list[Instruction] | Instruction) -> None:
    results = self._device.process(instructions)
    self._update_from_instructions(results)

  def _update_from_instructions(self, instructions: list[Instruction]) -> None:
    for instruction in instructions:
      match instruction.id:
        case Command.DEFINE_MACHINE:
          if instruction.input_value == 1:
            self._input_count = instruction.output_value
          elif instruction.input_value == 2:
            self._output_count = instruction.output_value
        case Command.PANEL_LOCK:
          self._is_locked = (instruction.input_value == 1)
        case Command.SWITCH_VIDEO:
          self._selected_source = instruction.input_value
        case Command.QUERY_OUTPUT_STATUS:
          self._selected_source = instruction.output_value
        case Command.QUERY_PANEL_LOCK:
          self._is_locked = (instruction.output_value == 1)
        case _:
          LOGGER.info('Discarded instruction: %s', instruction)
  
  def _update_instructions(self) -> list[Instruction]:
    return [
      # Queries the number of inputs
      Instruction(Command.DEFINE_MACHINE, 1, 1, self._machine_id),
      # Queries the number of outputs
      Instruction(Command.DEFINE_MACHINE, 2, 1, self._machine_id),
      # Queries which input is currently being routed to output 1
      Instruction(Command.QUERY_OUTPUT_STATUS, 0, 1, self._machine_id),
      # Queries the panel lock status
      Instruction(Command.QUERY_PANEL_LOCK, None, None, self._machine_id),
    ]


