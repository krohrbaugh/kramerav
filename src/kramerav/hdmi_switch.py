from typing import Protocol

DEFAULT_PORT = 5000

class HdmiSwitch(Protocol):
  """
  HDMI Switch Interface
  """

  def lock():
     """
     Lock panel
     """
     ...

  def unlock():
     """
     Unlock panel
     """

  def is_locked():
    """
    Returns `true` when panel is locked, `false` otherwise.
    """
    ...
