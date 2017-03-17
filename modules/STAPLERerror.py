class STAPLERerror(Exception):
    """Special error to be used in STAPLER.
"""
    pass


class VirtualIOError(Exception):
    """Error for when command object can not find usable input files.
    """
    pass