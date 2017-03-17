import copy
import itertools
import logging
import os

from GenericBase import GenericBase
import utils


class vcflib_vcfallelicprimitives(GenericBase):
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

    name = 'vcflib_vcfallelicprimitives'
    input_types = set(['.vcf'])
    output_types = ['.vcf']
    mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['-m', '-t', '-L', '-k', '-g']
    parallelizable = True
    help_description = '''
Sorry, no additional information on this tool.
    '''


    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'prefix')
        if run_command is None:
            final_cmd = [self.name]
        else:
            final_cmd = [run_command]
        for arg, val in self.out_cmd.iteritems():
            if arg in {'-i', '-o'}: continue
            final_cmd.append(arg + ' ' + val)
        final_cmd.append(self.out_cmd['-i'])
        final_cmd.append('> {0}'.format(self.out_cmd['-o']))
        return [' '.join(final_cmd)]
		