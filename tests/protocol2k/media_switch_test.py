from typing import Optional

from kesslerav.protocol2k.io import Command, Instruction
from kesslerav.protocol2k.media_switch import MediaSwitch

from fakes import FakeDevice

class TestMediaSwitch:
  def test_sets_machine_id_when_specified(self):
    expected_machine_id = 2

    (sut, _) = self.create_media_switch(machine_id = expected_machine_id)

    assert sut.machine_id == expected_machine_id

  def test_initializes_state_from_device(self):
    input_count = 8
    output_count = 2
    selected_source = 3
    fake_device = FakeDevice()
    response_instructions = [
      Instruction(Command.DEFINE_MACHINE, 1, input_count, 1),
      Instruction(Command.DEFINE_MACHINE, 2, output_count, 1),
      Instruction(Command.QUERY_OUTPUT_STATUS, 0, selected_source, 1),
      Instruction(Command.QUERY_PANEL_LOCK, 0, 1, 1),
    ]
    fake_device.response_instructions = response_instructions

    (sut, _) = self.create_media_switch(device = fake_device)

    assert sut.input_count == input_count
    assert sut.output_count == output_count
    assert sut.selected_source == selected_source
    assert sut.is_locked

  def test_update_reloads_state_from_device(self):
    input_count = 8
    output_count = 2
    selected_source = 3
    fake_device = FakeDevice()
    response_instructions = [
      Instruction(Command.DEFINE_MACHINE, 1, input_count, 1),
      Instruction(Command.DEFINE_MACHINE, 2, output_count, 1),
      Instruction(Command.QUERY_OUTPUT_STATUS, 0, selected_source, 1),
      Instruction(Command.QUERY_PANEL_LOCK, 0, 1, 1),
    ]
    fake_device.response_instructions = response_instructions

    (sut, _) = self.create_media_switch(device = fake_device)

    assert sut.input_count == input_count
    assert sut.output_count == output_count
    assert sut.selected_source == selected_source
    assert sut.is_locked

    # Device state changed
    input_count2 = 16
    output_count2 = 1
    selected_source2 = 12
    response_instructions2 = [
      Instruction(Command.DEFINE_MACHINE, 1, input_count2, 1),
      Instruction(Command.DEFINE_MACHINE, 2, output_count2, 1),
      Instruction(Command.QUERY_OUTPUT_STATUS, 0, selected_source2, 1),
      Instruction(Command.QUERY_PANEL_LOCK, 0, 0, 1),
    ]
    fake_device.response_instructions = response_instructions2

    sut.update()

    assert sut.input_count == input_count2
    assert sut.output_count == output_count2
    assert sut.selected_source == selected_source2
    assert not sut.is_locked

  def test_selected_source_sends_switch_video_instruction(self):
    input_count = 8
    output_count = 2
    initial_source = 7
    selected_source = 3
    fake_device = FakeDevice()
    response_instructions = [
      Instruction(Command.DEFINE_MACHINE, 1, input_count, 1),
      Instruction(Command.DEFINE_MACHINE, 2, output_count, 1),
      Instruction(Command.QUERY_OUTPUT_STATUS, 0, initial_source, 1),
    ]
    expected = [Instruction(Command.SWITCH_VIDEO, selected_source, 0, 1)]
    fake_device.response_instructions = response_instructions

    (sut, _) = self.create_media_switch(device = fake_device)
    fake_device.clear_instructions()

    sut.select_source(selected_source)

    assert sut.selected_source == selected_source
    assert fake_device.processed_instructions == expected

  def test_selected_source_normalizes_negative_value_to_0(self):
    input_count = 8
    output_count = 2
    initial_source = 7
    selected_source = -5
    expected_source = 0
    fake_device = FakeDevice()
    response_instructions = [
      Instruction(Command.DEFINE_MACHINE, 1, input_count, 1),
      Instruction(Command.DEFINE_MACHINE, 2, output_count, 1),
      Instruction(Command.QUERY_OUTPUT_STATUS, 0, initial_source, 1),
    ]
    expected = [Instruction(Command.SWITCH_VIDEO, expected_source, 0, 1)]
    fake_device.response_instructions = response_instructions

    (sut, _) = self.create_media_switch(device = fake_device)
    fake_device.clear_instructions()

    sut.select_source(selected_source)

    assert sut.selected_source == expected_source
    assert fake_device.processed_instructions == expected

  def test_selected_source_normalizes_sources_above_max_to_last_input(self):
    input_count = 8
    output_count = 1
    initial_source = 3
    selected_source = 10
    expected_source = 8
    fake_device = FakeDevice()
    response_instructions = [
      Instruction(Command.DEFINE_MACHINE, 1, input_count, 1),
      Instruction(Command.DEFINE_MACHINE, 2, output_count, 1),
      Instruction(Command.QUERY_OUTPUT_STATUS, 0, initial_source, 1),
    ]
    expected = [Instruction(Command.SWITCH_VIDEO, expected_source, 0, 1)]
    fake_device.response_instructions = response_instructions

    (sut, _) = self.create_media_switch(device = fake_device)
    fake_device.clear_instructions()

    sut.select_source(selected_source)

    assert sut.selected_source == expected_source
    assert fake_device.processed_instructions == expected

  def test_selected_source_updates_state_from_device(self):
    input_count = 8
    output_count = 1
    initial_source = 3
    selected_source = 6
    expected_source = 8
    fake_device = FakeDevice()
    fake_device.response_instructions = [
      Instruction(Command.DEFINE_MACHINE, 1, input_count, 1),
      Instruction(Command.DEFINE_MACHINE, 2, output_count, 1),
      Instruction(Command.QUERY_OUTPUT_STATUS, 0, initial_source, 1),
      Instruction(Command.QUERY_PANEL_LOCK, 0, 0, 1),
    ]
    expected = [Instruction(Command.SWITCH_VIDEO, selected_source, 0, 1)]
    (sut, _) = self.create_media_switch(device = fake_device)
    fake_device.clear_instructions()
    # Simulates the case where a source was requested, but something else
    # requested a different source (e.g., different thread, front panel) so
    # selected source ended up being different.
    fake_device.response_instructions = [
      Instruction(Command.SWITCH_VIDEO, selected_source, 0, 1),
      Instruction(Command.SWITCH_VIDEO, expected_source, 0, 1),
      Instruction(Command.PANEL_LOCK, 1, 0, 1),
    ]

    sut.select_source(selected_source)

    assert sut.selected_source == expected_source
    assert sut.is_locked
    assert fake_device.processed_instructions == expected

  def test_lock_sends_lock_instruction(self):
    expected = [Instruction(Command.PANEL_LOCK, 1, 0, 1)]
    (sut, fake_device) = self.create_media_switch()
    fake_device.clear_instructions()

    sut.lock()

    assert sut.is_locked
    assert fake_device.processed_instructions == expected

  def test_lock_updates_state_from_device(self):
    input_count = 8
    output_count = 1
    initial_source = 3
    expected_source = 6
    fake_device = FakeDevice()
    fake_device.response_instructions = [
      Instruction(Command.DEFINE_MACHINE, 1, input_count, 1),
      Instruction(Command.DEFINE_MACHINE, 2, output_count, 1),
      Instruction(Command.QUERY_OUTPUT_STATUS, 0, initial_source, 1),
      Instruction(Command.QUERY_PANEL_LOCK, 0, 0, 1),
    ]
    expected = [Instruction(Command.PANEL_LOCK, 1, 0, 1)] # Lock
    (sut, _) = self.create_media_switch(device = fake_device)
    fake_device.clear_instructions()
    # Simulates the case where panel lock was requested, but something else
    # requested a other changes (e.g., different thread, front panel) so
    # panel lock and source end up being different.
    fake_device.response_instructions = [
      Instruction(Command.PANEL_LOCK, 1, 0, 1), # Lock
      Instruction(Command.SWITCH_VIDEO, expected_source, 0, 1),
      Instruction(Command.PANEL_LOCK, 0, 0, 1), # Unlock
    ]

    sut.lock()

    assert sut.selected_source == expected_source
    assert not sut.is_locked
    assert fake_device.processed_instructions == expected

  def test_unlock_sends_unlock_instruction(self):
    expected = [Instruction(Command.PANEL_LOCK, 0, 0, 1)]
    (sut, fake_device) = self.create_media_switch()
    fake_device.clear_instructions()

    sut.unlock()

    assert not sut.is_locked
    assert fake_device.processed_instructions == expected

  def test_unlock_updates_state_from_device(self):
    input_count = 8
    output_count = 1
    initial_source = 6
    expected_source = 2
    fake_device = FakeDevice()
    fake_device.response_instructions = [
      Instruction(Command.DEFINE_MACHINE, 1, input_count, 1),
      Instruction(Command.DEFINE_MACHINE, 2, output_count, 1),
      Instruction(Command.QUERY_OUTPUT_STATUS, 0, initial_source, 1),
      Instruction(Command.QUERY_PANEL_LOCK, 0, 0, 1),
    ]
    expected = [Instruction(Command.PANEL_LOCK, 0, 0, 1)] # Unlock
    (sut, _) = self.create_media_switch(device = fake_device)
    fake_device.clear_instructions()
    # Simulates the case where panel lock was requested, but something else
    # requested a other changes (e.g., different thread, front panel) so
    # panel lock and source end up being different.
    fake_device.response_instructions = [
      Instruction(Command.PANEL_LOCK, 0, 0, 1), # Unlock
      Instruction(Command.SWITCH_VIDEO, expected_source, 0, 1),
      Instruction(Command.PANEL_LOCK, 1, 0, 1), # Lock
    ]

    sut.unlock()

    assert sut.selected_source == expected_source
    assert sut.is_locked
    assert fake_device.processed_instructions == expected
  
  def create_media_switch(
      self,
      device = FakeDevice(),
      machine_id: Optional[int] = 1
    ) -> tuple[MediaSwitch, FakeDevice]:
    return (MediaSwitch(device, machine_id), device)

