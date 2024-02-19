from typing import Protocol

class MediaSwitch(Protocol):
  """
  Representation of a multi-input, single- or fixed-output media switch, such as a
  5x1 HDMI switch, or a 5x2 HDMI switch where the output on both ports is always the same.

  Example Kramer devices: VS-41H, VS-81H, VS-161H
  """

  def select_source(self, input: int) -> None:
    """
    Select the specified video input
    """

  def lock(self):
     """
     Lock front panel
     """

  def unlock(self):
     """
     Unlock front panel
     """

  def update(self) -> None:
    """
    Refresh device state.
    """

  @property
  def selected_source(self) -> int:
    """
    Returns the input number of the selected source
    """

  @property
  def is_locked(self) -> bool:
    """ Returns `true` when front panel is locked, `false` otherwise.
    
    Note that the device can still be controlled remotely when front panel is
    locked.
    """

  @property
  def input_count(self) -> int:
    """
    Returns the number of inputs the switch has
    """

  @property
  def output_count(self) -> int:
    """
    Returns the number of outputs the switch has
    """
