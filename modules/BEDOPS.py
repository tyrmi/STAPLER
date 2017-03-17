from GenericBase import GenericBase

class BEDOPS_(GenericBase):
    """Class for generic command lines, also superclass for STAPLER input classes.

    Arguments:
    in_cmd: String containing a command line
    in_dir: Directory object containing input files
    out_dir: Directory object containing output files
    NOTICE! Keep the directory objects up to date about file edits!

    Attributes:
    name: Name of the function.
    input_type: Input types accepted by this application.
    output_types: List of output types produced by the application.
    mandatory_args: Args the user be provided in in_cmd when initializing.
    user_mandatory_args: Args the user must provide.
    remove_user_args: Args that will be removed from the final command.
    optional_args: Args that may be part of the command line.
    in_cmd: Command entered by user.
    parsed_cmd: Final output command as option:value dict.
    file_names: Names of output files.
    id: Bare name of input file (without the possible ending).


    Methods:
    get_cmd: Method for getting the final cmd line string for output.
    """

    name = 'BEDOPS_vcf2bed'
    #Accept all defined types:
    input_types = set(['.vcf'])
    output_types = ['.bed']
    mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = []
    parallelizable = True
    help_description = '''
Sorry no additional specific help available for this
tool :(

See the original tool manual for help!
    '''

    def __init__(self, in_cmd, in_dir, out_dir):
        raise NotImplementedError('Not implemented yet')
