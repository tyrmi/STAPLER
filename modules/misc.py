from GenericBase import GenericBase

class vcf_sort(GenericBase):
    """Class for using unix sort command on vcf files.

    Parameters:
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
    command_ids: File names of input file(s) with no file extensions.


    Methods:
    get_cmd: Method for getting the final cmd line string for output.
    """

    name = 'stapler_vcf_sort'
    input_types = set(['.vcf'])
    output_types = ['.vcf']
    hidden_mandatory_args = ['-i', '-o']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    user_optional_args = []
    parallelizable = True
    help_description = '''
This tool uses unix sort command to sort vcf files.

The config.txt should not be edited for this command as the used
unix sort command is a standard command line tool which should be available in
any unix and unix-like platform.
'''



    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        final_cmds = ['grep --no-filename "#" {0} > {1}\n'.format(self.out_cmd['-i'],
                                                                  self.out_cmd['-o'])]
        final_cmds.append('grep --no-filename -v "#" {0} | sort -k1,1V -k2,2n >> {1}\n'.format(self.out_cmd['-i'],
                                                                                               self.out_cmd['-o']))
        return final_cmds

