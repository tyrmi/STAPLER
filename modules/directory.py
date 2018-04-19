import fnmatch
import logging
import os

import STAPLERerror
import utils

class Directory():
    """A model of directory, which can contain other directories and files.

    Methods:
    add_file
    use_file
    file_pairs
    get_absolute_file_path
    __generate_unique_id

    Attributes:
    _current_id: A class variable containign base integer for generating unique identifier for directories
    path: The directory path.
    files: A list of file instances located in this directory
    file_names: A dictionary of name:instance located in this directory
    _file_pairs: A dictionary of {pairing_rule_string : [file_instance_1, file_instance_2]}
    as keys and file instances as values
    directories: A list of directory instances located in this directory
    directory_names: A dictionary of directories located in this directory with
    directory names as keys and file instances as values
    users: a list of tools using this directory as an input
    entry_types: Set of file types found in this dir
    """

    def __init__(self, path, users=None, create_dir=True):
        """
        Parameters:
        path: Absolute path to folder.
        users: List of ids using this directory as an input
        create_dir: A bool indicating if the directory should be created if
        it does not exist

        Raises:
        STAPLERerror: Raised if path does not point to an empty dir.
        ValueError: Raised if file paths are absolute.
        """
        self.path = path.strip()
        self.files = []
        self.file_names = {}
        self._file_pairs = {}
        self.entry_types = set()
        self.dirs = []
        self.directory_names = {}
        if users is not None:
            self.users = users
        else:
            self.users = []
        if os.path.exists(path) and not os.path.isdir(path):
            raise ValueError('An entry with name {0} exists but it is not a directory'.format(path))

        # Add necessary information about the contents of existing directory.
        if os.path.isdir(path):
            for entry in os.listdir(path):
                # Skip hidden entries
                if entry.startswith('.'): continue
                if os.path.isfile(os.path.join(path, entry)):
                    self._add_existing_file(entry)
                elif os.path.isdir(os.path.join(path, entry)):
                    self.add_dir(entry)
        elif create_dir:
            try:
                os.mkdir(path)
            except OSError as e:
                raise STAPLERerror.STAPLERerror('Unable to create a new dir '
                                                'to location with error '
                                                'message:\n{0}'.format(str(e)))


    def _add_existing_file(self, fl_name, file_id = None):
        """Adds an existing file to the directory instance.

        Parameters:
        fl_name: Name of the file.

        Raises:
        ValuerError: If a file with same name exists already, file path is
        absolute or path exists but is not a file.

        Side-effects:
        Adds a new file to the directory instance
        """
        if os.path.isabs(fl_name):
            raise ValueError('File name is absolute path:\n{0}'.format(fl_name))
        absolute_path = os.path.join(self.path, fl_name)
        assert os.path.isfile(absolute_path)
        new_file = File(os.path.join(self.path, fl_name), fl_name, file_id)
        self.files.append(new_file)
        self.file_names[fl_name] = new_file
        self.entry_types.add(utils.splitext(fl_name)[1])



    def add_file(self, fl_name, file_id = None):
        """Adds a new file to the directory instance.

        Parameters:
        fl_name: Name of the file.

        Raises:
        ValuerError: If a file with same name exists already, file path is
        absolute or path exists but is not a file.

        Side-effects:
        Adds a new file to the directory instance
        """
        assert not os.path.isabs(fl_name)
        absolute_path = os.path.join(self.path, fl_name)
        assert not os.path.isdir(absolute_path)
        # Intead of assertion a specific error is raised as this is used in
        # detecting which workflows have been successfully run and which have
        #  not
        if os.path.exists(absolute_path):
            raise STAPLERerror.NewFileExists(fl_name)
        if fl_name in self.file_names:
            raise STAPLERerror.STAPLERerror('Error! File with name {0} '
                                            'is predicted to be created twice '
                                            'to output directory {1}. Make '
                                            'sure that 1) you do not have '
                                            'input files with identical base '
                                            'names but differing file '
                                            'extensions in the input directory '
                                            'and 2) that you do not manually '
                                            'define output file paths, as these '
                                            'are automatically inferred by '
                                            'STAPLER.'.format(fl_name, self.path))
        new_file = File(os.path.join(self.path, fl_name), fl_name, file_id)
        self.files.append(new_file)
        self.file_names[fl_name] = new_file
        self.entry_types.add(utils.splitext(fl_name)[1])


    def rm_file(self, fl_name):
        """Removes a file from the directory instance.

        This call does not actually remove files from the file system.
        rm_file can be called for instance when file is predicted to be
        removed by a command. For instance the unix commad below will
        remove input file myfile.txt.gz when creating the uncompressed
        output:
        gzip -d myfile.txt.gz

        :param fl_name:
        :return:
        """
        self.files.remove(self.file_names[fl_name])
        del self.file_names[fl_name]

        # Check if any files remain in the dir with the current file
        # extension.
        extension = utils.splitext(fl_name)[1]
        for name in self.file_names.keys():
            if name.endswith(extension):
                return
        # No more files with the current extension exist in the dir,
        # remove the extension from entry_types set.
        print self.entry_types
        self.entry_types.remove(extension)


    def add_dir(self, dir_name, dir_id = None):
        """Adds a new directory to the folder.

        Parameters:
        fl_name: Name of the directory.

        Raises:
        ValueError: If a directory with same name exists already, directory
        path is absolute or path exists but is not directory.
        """
        dir_name = dir_name.rstrip('/')
        if dir_name in self.directory_names:
            raise ValueError('Directory with name {0} already '
                             'exists in the folder:\n{1}'.format(dir_name,
                                                                 self.path))
        if os.path.isabs(dir_name):
            raise ValueError('Directory name is absolute path:\n{0}'.format(dir_name))

        absolute_path = os.path.join(self.path, dir_name)
        if os.path.isdir(absolute_path):
            new_directory = Directory(os.path.join(absolute_path), dir_id)
            self.dirs.append(new_directory)
            self.directory_names[dir_name] = new_directory
            # Intepret directory names with dot as having a file extension
            # This bahavior is because some tools take directories instead of
            # files as inputs, and the directory "type" must be identified
            if os.path.splitext(dir_name)[1]:
                self.entry_types.add(os.path.splitext(dir_name)[1])
        elif os.path.exists(absolute_path) and not os.path.isdir(absolute_path):
            raise ValueError('Path exists but is not a directory!')


    def use_file(self, fl_name, user_tool_name):
        """Adds a new user to specific file.

        Parameters:
        fl_name: Name of the file in question.
        user_tool_name: Name of the user tool.
        """
        self.file_names[fl_name].users.append(user_tool_name)


    def get_absolute_file_path(self, file_name):
        """Returns the absolute path to requested file found in this folder.

        Parameters:
        file_name: Name of the file for which abs path is requested.
        Returns:
        String containing the absolute path.
        """
        assert file_name in self.files
        return os.path.join(self.path, file_name)


    def file_pairs(self, pattern='_R?', user=None, file_formats=None,
                   exclusion_iterable=None):
        """Finds pairs for paired end files within this directory.

        Parameters:
        pattern: Pattern to look for from the files. Pair 1 should have 1 and
        pair 2 a 2 in place of ?.
        """
        if user is None:
            user = []
        if file_formats is None:
            file_formats = []
        if exclusion_iterable is None:
            exclusion_iterable = []
        pair_identifier = (pattern, tuple(user), tuple(file_formats), tuple(exclusion_iterable))
        try:
            return self._file_pairs[pair_identifier]
        except KeyError:
            self._file_pairs[pair_identifier] = utils.find_pairs(self, pattern, user, file_formats, exclusion_iterable)
            return self._file_pairs[pair_identifier]


class File():
    """A model of a file.

    Methods:
    __generate_unique_id

    Attributes:
    _current_id: A class variable containign base integer for generating unique identifier for directories
    abs_path: absolute file path
    name: the name of the file

    """
    def __init__(self, abs_path, name, users=None):
        self.abs_path = abs_path
        self.name = name
        if users is not None:
            self.users = users
        else:
            self.users = []

