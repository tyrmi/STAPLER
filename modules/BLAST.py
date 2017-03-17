import os

from GenericBase import GenericBase
from STAPLERerror import STAPLERerror
from STAPLERerror import VirtualIOError
import utils

class blast(GenericBase):
    name = 'blast'
    input_types = {'.fasta'}
    output_types = ['.out', '.xml']
    mandatory_args = ['-query', '-out']
    user_mandatory_args = []
    remove_user_args = user_mandatory_args
    optional_args = ['--!pb', '--!blastn', '--!tblastn', '--!blastp', '-db',
                     '-dbnuc', '-dbprot', '-query_loc',
                     '-strand', '-task', '-evalue', '-word_size', '-gapopen',
                     '-gapextend', '-penalty', '-reward', '-use_index',
                     '-index_name', '-subject', '-subject_loc', '-outfmt',
                     '-show_gis', '-num_descriptions', '-num_alignments',
                     '-html', '-dust', '-filtering_db',
                     '-windows_masker_taxid', '-window_masker_db',
                     '-soft_masking', '-lcase_masking', '-gilist',
                     '-seqidlist', 'negative_gilist', '-entrez_query',
                     '-db_soft_mask', '-db_hard_mask', '-perc_identity',
                     '-culling_limit', '-best_hit_overhang',
                     '-best_hit_score_edge', '-max_target_seqs',
                     '-template_type', '-template_length', '-dbsize',
                     '-searchsp', '-max_hsps', '-sum_statistics',
                     '-import_search_strategy', '-xdrop_ungap', '-xdrop_gap',
                     '-xdrop_gap_final', '-no_greedy',
                     '-min_raw_gapped_score', '-ungapped', 'window_size',
                     '-off_diagonal_range', 'parse_deflines', '-remote']
    parallelizable = True
    help_description = '''
Tested with BLAST 2.2.29

Notice! This tool does not allow for prefixes in installation_config.txt!
BLAST must be in unix PATH instead.

--!blastn, --!tblastn or --!blastp must be included in each command line.

Parallel blast can be used by adding the --!pb parameter.

".xml" file extension is used when "-outfmt 5" is included in the command.
Otherwise the output file extension is ".out".

If you wish to use a local database, you must create it beforehand manually by
using the "makeblastdb" command.
    '''

    def _select_IO(self, out_cmd, in_dir, out_dir):
        """Returns a dict containing the proper IO commands.

        This method must keep the directory objects up to date of the file
        edits!

        Arguments:
        in_cmd: A dict containing the command line.
        in_dir: Input directory.
        out_dir: Output directory.

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
                    IO_files['-query'] = os.path.join(in_dir.path, fl_name)
                    in_dir.use_file(fl_name, self.name)
                    if '-outfmt' in out_cmd:
                        if out_cmd['-outfmt'] == '5':
                            output_name = utils.splitext(fl_name)[0] + \
                                  self.output_types[1]
                    else:
                        output_name = utils.splitext(fl_name)[0] + \
                                      self.output_types[0]
                    output_path = os.path.join(out_dir.path, output_name)
                    IO_files['-out'] = output_path
                    file_names.add(output_name)
                    out_dir.add_file(output_name)
                    break
        if not IO_files:
            raise VirtualIOError('No more unused input files')
        out_cmd.update(IO_files)
        return out_cmd, file_names


    def get_cmd(self):
        """Returns the final command line.

        Returns:
        final_cmd: List of command line produced by the object (line breaks not allowed within command lines!).
        """
        run_command = utils.parse_config(self.name, 'cmd_name', 'prefix')
        if run_command:
            raise STAPLERerror('{0} does not allow a prefixes. {0} must be added '
                          'to PATH instead!')

        #Add pb if set by user
        if '--!pb' in self.out_cmd:
            final_cmd = ['pb']
        else:
            final_cmd = []

        #Select program
        if '--!blastn' in self.out_cmd:
            final_cmd.append('blastn')
        elif '--!tblastn' in self.out_cmd:
            final_cmd.append('tblastn')
        elif '--!blastp' in self.out_cmd:
            final_cmd.append('blastp')
        else:
            raise STAPLERerror('Parallel blast must contain argument --!blastn, '
                          '--!tblastn or --!blastp, but none was found!')

        for arg, val in self.out_cmd.iteritems():
            if arg in ('--!blastn', '--!blastp', '--!tblastn', '--!pb'):
                continue
            final_cmd.append(arg + ' ' + val)
        return [' '.join(final_cmd)]
		