import enum


@enum.unique
class HdmiGroup(enum.IntEnum):
    AUTO = 0
    CEA = 1
    DMT = 2