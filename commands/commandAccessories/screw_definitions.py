from enum import Enum


class ScrewDefinition:
    """
    Define a Screw Definition for the hole in the anchors
    name: The name of the screw type
    headDiameter: The diameter of the head of the screw
    holeDiameter: The diameter of the hole for the screw
    countersinkAngle: The angle of the countersink for the screw
    """

    def __init__(self, displayName, headDiameter, holeDiameter, countersinkAngle):
        self.displayName = displayName
        self.headDiameter = headDiameter
        self.holeDiameter = holeDiameter
        self.countersinkAngle = countersinkAngle


class ScrewDefinitionsEnum(Enum):
    """
    Some Common Screw Definitions, defined in CM
    """

    M3 = ScrewDefinition("M3 Countersunk", 0.6, 0.32, 90)
    M4 = ScrewDefinition("M4 Countersunk", 0.8, 0.42, 90)
    M5 = ScrewDefinition("M5 Countersunk", 1, 0.52, 90)
    STOVE_SCREW_3_16 = ScrewDefinition("3/16 Countersunk Stove Screw", 1, 0.52, 82)
    # UNC1_4_20 = ScrewDefinition("1/4-20", 1.2, 0.64, 82) # too big for offset anchor

    @classmethod
    def list(cls):
        return list(map(lambda s: s.value, cls))

    @classmethod
    def byName(cls, displayName):
        for s in cls.list():
            if displayName == s.displayName:
                return s
