from typing import Optional

from ..constants import LOGGER
from ..media_switch import MediaSwitch as MediaSwitchProtocol
from .io import Command, Instruction, TcpDevice

class MediaSwitch(MediaSwitchProtocol):
    def __init__(self, device: TcpDevice, machine_id: Optional[int] = None, output_number: Optional[int] = 1):
        self._device = device
        self._machine_id = machine_id
        self._is_locked = False
        self._selected_video_source = 0
        self._selected_audio_source = 0
        self._input_count = 0
        self._output_count = 0
        self._output_number = output_number # A matrix is represented by a MediaSwitch instance for each output.
        self.update()

    def _normalize_value(self, value):
        if value < 0:
            value = 0
        elif value > self._input_count:
            value = self._input_count
        return value

    def select_source(self, input: int) -> None:
        """
        Select the specified video and audio input
        """
        normalized_input = self._normalize_value(input)
        instruction = Instruction(
            Command.SWITCH_VIDEO,
            normalized_input,
            self._output_number+1, # We're counting from zero, the switch is counting from one
            self._machine_id)
        instruction = Instruction(
            Command.SWITCH_AUDIO,
            normalized_input,
            self._output_number+1,
            self._machine_id)
        self._process(instruction)
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
        return self._selected_video_source

    @property
    def selected_audio_source(self) -> int:
        """
        Returns the input number of the selected audio source
        """
        return self._selected_audio_source

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
                    self._selected_video_source = instruction.input_value
                case Command.SWITCH_AUDIO:
                    self._selected_audio_source = instruction.input_value
                case Command.QUERY_VIDEO_OUTPUT_STATUS:
                    self._selected_video_source = instruction.output_value
                case Command.QUERY_AUDIO_OUTPUT_STATUS:
                    self._selected_audio_source = instruction.output_value
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
            # Queries which input is currently being routed to output represented by this instance (output one, if it's not a matrix switcher)
            Instruction(Command.QUERY_VIDEO_OUTPUT_STATUS, 0, self._output_number, self._machine_id),
            Instruction(Command.QUERY_AUDIO_OUTPUT_STATUS, 0, self._output_number, self._machine_id),
            # Queries the panel lock status
            Instruction(
                Command.QUERY_PANEL_LOCK,
                None,
                None,
                self._machine_id),
        ]
