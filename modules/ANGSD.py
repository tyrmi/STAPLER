import copy
import itertools
import logging
import os

from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import directory
import utils


class ANGSD():
    """Class for using ANGSD software.

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

    name = 'ANGSD'
    #Accept all defined types:
    input_types = set(['.bam'])
    output_types = ['.out']
    mandatory_args = []
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['-i', '-bam', '-r', '-rf', '-remove_bads', '-nInd',
                     '-nLines', '-uniqueOnly', '-show', '-minMapQ', '-minQ',
                     '-only_proper_pairs', '-C', '-baq', '-minMaf',
                     '-SNP_pval', '-minInd', '-setMinDepth', '-setMaxDepth',
                     '-geno_minDepth', '-trim', '-doMaf', '-doDepth',
                     '-maxDepth', '-doQsDist', '-doFasta']
    parallelizable = True
    help_description = '''
    No additional help! Sorry!
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Returns a dict containing the proper IO commands.

        This method must keep the directory objects up to date of the file
        edits!

        Arguments:
        in_cmd: A dict containing the command line.
        in_dir: Input directory (instance of filetypes.Directory).
        out_dir: Output directory (instance of filetypes.Directory).

        Returns:
        out_cmd: Dict containing the output commands
        file_names: Names of the output files.

        Raises:
        VirtualIOError: No valid input file can be found.
        """

        IO_files = {}
        file_names = set()
        for fl_name, users in in_dir.files.iteritems():
            if self.name not in users:
                if utils.splitext(fl_name)[-1] in self.input_types:
                    IO_files['-i'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    assert len(self.output_types) == 1, 'Several output ' \
                                                        'types, override ' \
                                                        'this method!'

                    output_name = utils.splitext(fl_name)[0] + \
                                  self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-o'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names