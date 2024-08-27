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

    def _normalize_value(self, value):
        if value < 0:
            value = 0
        elif value > self._input_count:
            value = self._input_count
        return value

    def select_source(self, input: int) -> None:
        """
        Select the specified video input
        """
        normalized_input = self._normalize_value(input)
        instruction = Instruction(
            Command.SWITCH_VIDEO,
            normalized_input,
            1,
            self._machine_id)
        self._selected_source = normalized_input
        self._process(instruction)

    def lock(self):
        """
        Lock panel
        """
        instruction = Instruction(
            Command.PANEL_LOCK, 1, None, self._machine_id)
        self._is_locked = True
        self._process(instruction)

    def unlock(self):
        """
        Unlock panel
        """
        instruction = Instruction(
            Command.PANEL_LOCK, 0, None, self._machine_id)
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
    def machine_id(self) -> int | None:
        return self._machine_id

    def _process(self, instructions: list[Instruction] | Instruction) -> None:
        results = self._device.process(instructions)
        self._update_from_instructions(results)

    def _update_from_instructions(
            self, results: list[Instruction]) -> None:
        for instruction in results:
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
            Instruction(Command.QUERY_OUTPUT_STATUS, 0, 2, self._machine_id),
            # Queries the panel lock status
            Instruction(
                Command.QUERY_PANEL_LOCK,
                None,
                None,
                self._machine_id),
        ]


class MediaMatrix(MediaSwitch):
    def __init__(self, device, output_count, machine_id: Optional[int] = None):
        self._matrix = [0] * output_count
        super().__init__(device, machine_id)
        self._output_count = output_count

    def set_route(self, input: int, output: int) -> None:
        """
        Select the specified input
        """
        normalized_input = self._normalize_value(input)
        normalized_output = self._normalize_value(output)
        instruction = Instruction(
            Command.SWITCH_VIDEO,
            normalized_input,
            normalized_output,
            self._machine_id)
        self._process(instruction)
        instruction = Instruction(
            Command.SWITCH_AUDIO,
            normalized_input,
            normalized_output,
            self._machine_id)
        self._process(instruction)
        self._matrix[output] = normalized_input

    @property
    def routing_table(self):
        return self._matrix

    def update(self) -> None:
        super().update()
        # Always update state of matrix each time because order can get scrambled otherwise TODO find a cleverer way...
        for i in range(self.output_count):
            self._matrix[i] = self._device.process(Instruction(Command.QUERY_OUTPUT_STATUS, 0, i+1, self._machine_id))[0].output_value


    def _update_from_instructions(self, results: list[Instruction]) -> None:
        for instruction in results:
            match instruction.id:
                case Command.DEFINE_MACHINE:
                    if instruction.input_value == 1:
                        self._input_count = instruction.output_value
                    elif instruction.input_value == 2:
                        self._output_count = instruction.output_value
                case Command.PANEL_LOCK:
                    self._is_locked = (instruction.input_value == 1)
                case Command.SWITCH_VIDEO:
                    self._matrix[instruction.output_value] = instruction.input_value
                case Command.QUERY_PANEL_LOCK:
                    self._is_locked = (instruction.output_value == 1)
                case _:
                    LOGGER.info('Discarded instruction: %s', instruction)

    def _update_instructions(self) -> list[Instruction]:
        instructions = [
            # Queries the number of inputs
            Instruction(Command.DEFINE_MACHINE, 1, 1, self._machine_id),
            # Queries the number of outputs
            Instruction(Command.DEFINE_MACHINE, 2, 1, self._machine_id),
            # Queries the panel lock status
            Instruction(
                Command.QUERY_PANEL_LOCK,
                None,
                None,
                self._machine_id),
        ]
        return instructions
