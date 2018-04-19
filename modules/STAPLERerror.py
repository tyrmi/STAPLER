class STAPLERerror(Exception):
    """Special error to be used in STAPLER.
    """
    pass


class VirtualIOError(Exception):
    """Error for when command object can not find usable input files.
    """
    pass


class NewDirExists(Exception):
    """New file is being added to Directory, but file exists already.
    """
    pass


class NewFileExists(Exception):
    """New file is being added to Directory, but file exists already.
    """
    pass


class NotConfiguredError(Exception):
    """Configuration file contains an unexpected 'none' as execute field.
    """
    pass
