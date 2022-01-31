import enum


@enum.unique
class WifiMode(enum.IntEnum):
    OFF = 0
    AP = 1
    CLIENT = 2