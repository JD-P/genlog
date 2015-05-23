"""
Copyright (C) 2015 John David Pressman

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

#!/usr/bin/python3

import time,datetime


import json


import os


import sys


import re


import importlib


import zipfile


import pprint


class Logger():
    """Implements the core logging facilities."""
    def __init__(self, interface):
        self.interface = interface

    def import_from_path(self, modpath, path):
        """Import the module modname from path without side effects at end of
        execution. (But has side effects during.) modpath *must* be a fully 
        qualified pkgname."""
        oldcache = sys.modules.copy()
        sys.path.append(path)
        pathsplit = modpath.rsplit(".", 1)
        if len(pathsplit) == 1:
            script = importlib.import_module(pathsplit[0])
        else:
            _from = pathsplit[0]
            _import = pathsplit[1]
            script = importlib.import_module(_import, _from)
        sys.path.pop() 
        sys.modules = oldcache
        return script


    def getfields(self, settings, logname):
        """Extract the fields from a logger settings.conf file and convert them
        into field objects using cascading types.

        The following are information about variables in this function:

        fields: A key in the settings.conf that holds the list of field 
        descriptions.

        fdict: A dictionary that describes a field.

        fobject: A Field object constructed from the fdict. 

        fname: The name of the field. Used as default in place of flabel and
        olabel if they're not set. Also used to generate do_ methods for Cli
        interface.

        flabel: The 'description' of the field that is used by the interface
        to give a textual description to the user of what sort of input is
        expected in the field.

        olabel: The label that is used above the column when it's printed as
        text.

        ftype: The field type of the field and of the column. The type is a sort
        of template for fields that lets you style a new field after an old one.

        restrictions: The regex that determines what inputs are valid.

        onmatch: Says whether strings evaluated by the regex should or should not
        be matched by it.

        oformat: The name of the script in either this logs _scripts or the
        global _scripts namespace that determines how the column should be 
        printed for text output.

        search: The name of the script in either this logs _scripts or the
        global _scripts namespace that determines how the column should be
        searched through when given a search string.

        flist: The list of field objects returned by getfields."""
        flist = []
        fields = settings["fields"]
        for field in fields:
            fdict = {}
            cascade = self.get_ancestors(Logger, field, logname)
            cascade.reverse()
            cascade.append(field)
            for field in cascade:
                for key in field:
                    try:
                        fdict[key]
                    except KeyError:
                        fdict[key] = None
                    fdict[key] = field[key] if field[key] else fdict[key]
            fobject = Field.from_fdict(Field, fdict)
            fobject.unpack_scripts(logname=logname)
            flist.append(fobject)
        return flist

    def readconf(self, logger):
        """Read the configuration file at ~/.loggers/<LOGGER>/settings.conf and return the settings."""
        paths = self.genpaths(logger)
        # If config file already exists, read from it. If not, create it.
        # If directory for loggers doesn't exist, create it.
        try:
            config = open(paths["confpath"], 'r')
        except IOError:
            if os.path.isdir(paths["logdir"]):

                settings = {"jsonpath":paths["jsonpath"], "txtpath":paths["txtpath"]}
                json.dump(settings, config)
                config.close()
                return settings
            else:
                os.makedirs(paths["logdir"])
                self.readconf()
        # Verify the config file is valid JSON
        try:
            settings = json.load(config)
        except ValueError:
            raise ValueError("The configuration file is corrupted or not valid JSON.")
        config.close()
        return settings

    def load_log(self, logname):
        """Return the json of the log for logname."""
        paths = self.genpaths(logname)
        jsonpath = paths["jsonpath"]
        logfile = open(jsonpath, 'r')
        log = json.load(logfile)
        return log

    def load_log_entries(self, logname, entries, fields):
        """Load the log entries from logname given by the list of ranges
        in <entries>."""
        log = self.load_log(logname)
        for findex in range(0, len(fields)):
            field = fields[findex]
            column = log[findex]
            if field["fname"] != column["fname"]:
                raise ValueError("Order of columns has become corrupted/assumptions"
                                 " about data have been violated.")
        log_entries = set()
        for _range in entries:
            start = _range[0]
            end = (_range[-1] + 2)
            inclusive_range = range(start, end)
            for entry in inclusive_range:
                edict = {}
                for column in log:
                    fname = column["fname"]
                    edict[fname] = column["data"][entry]
                log_entries.add((entry, edict))
        return log_entries
        
    def add_entry(self, entry, logname):
        """Take an entry dictionary and write out to a JSON log based on it."""
        paths = self.genpaths(logname)
        logpath = paths["jsonpath"]
        try:
            jlog = open(logpath, 'r')
            logdata = json.load(jlog)
        except IOError:
            self.loginit(log)
        except EOFError:
            self.loginit(log)
        except ValueError:
            print("JSON log file exists, but is empty. Initalizing log file.")
            self.loginit(log)
        jlog.close()
        # FINISH WHEN YOU KNOW WHAT SORT OF DATA SINGLE LOG SESSION RETURNS
        jlog = open(log,'w')
        json.dump(jlist,jlog)
        jlog.close()
        return 0

    def genpaths(self, logger):
        """Build the paths, confdir is used to check for errors."""
        paths = {}
        paths["homedir"] = os.path.expanduser("~")
        paths["confdir"] = os.path.join(paths["homedir"], ".loggers/")
        paths["logdir"] = os.path.join(paths["confdir"], logger)
        paths["confpath"] = os.path.join(paths["logdir"], "settings.conf")
        paths["jsonpath"] = os.path.join(paths["logdir"], (logger + "-log.json"))
        paths["txtpath"] = os.path.join(paths["homedir"], "Documents/", (logger + "-log.txt"))
        return paths

    def loginit(self, jsonpath):
        """Initalize the log file if it has no prior entries."""
        logfilename = os.path.split(jsonpath)[1]
        logger = logfilename.split("-")[0]
        jlog = open(jsonpath,'a')
        settings = self.readconf(logger)
        flist = self.getfields(settings)
        edict = log(flist)
        jlist = [edict]
        json.dump(jlist,jlog)
        quit()

    def available_fields(self, logger):
        """Return the available field types."""
        # In what namespace? O_o
        pass

    def search_tree(self, tree, search_name, logname):
        """Search a given tree for a given name. Trees are the abstract search
        path used in cascading namespace searching where the local directory is
        searched for first and then the global directory searched second. See 
        the manual for more information. Returns the path that contains the 
        item being searched for.

        tree: The name of the directory that should be searched on the abstract
        path.

        search_name: The name of the script/field/etc that's being searched for
        in the 'tree' directory.

        logname: The name of the local logger.
        """
        def search_node(tree, search_name, nodepath):
            """Search an individual node in the tree."""
            treedir = os.path.join(nodepath, tree)
            try:
                files = os.listdir(treedir)
            except OSError:
                raise ValueError("Was passed an improper tree name.")
            for _file in files:
                if _file.split(".")[0] == search_name:
                    return treedir
                else:
                    return False
        
        paths = self.genpaths(logname)
        logdir = paths["logdir"]
        confdir = paths["confdir"]
        localnode = search_node(tree, search_name, logdir)
        if localnode:
            return localnode
        globalnode = search_node(tree, search_name, confdir)
        if globalnode:
            return globalnode
        else:
            return False
            

    def get_ancestors(self, field, logname):
        """Get the ancestors of a given field."""
        def get_ancestor(self, field, logname):
            name = field["name"]
            ftype = field["type"]
            if name == ftype:
                return False
            else:
                contain_dir = self.search_tree('_ftypes', ftype, logname)
                if not contain_dir:
                    raise ValueError("No field of this type in local or global"
                                     " namespace.")
                fullpath = os.path.join(contain_dir, (ftype + ".json"))
                grave = open(fullpath, 'r')
                ancestor = json.load(grave)
                grave.close()
                return ancestor
        ancestors = []
        ancestor = get_ancestor(self, field, logname)
        while ancestor:
            ancestors.append(ancestor)
            if ancestor["name"] == ancestor["type"]:
                return ancestors
            else:
                ancestor = get_ancestor(self, field, logname)

    def get_script(self, script, logname):
        """Return a script from the scripts name given as a string and the
        logname of the local logger."""
        contain_dir = self.search_tree('_scripts', script, logname)
        if not contain_dir:
            raise ValueError("No script by name " + script + "in local or global"
                             " namespace.")
        imported_script = self.import_from_path(script, contain_dir)
        return imported_script

    def verify_logname(self, logname):
        """Verify that the user typed in a valid logname."""
        paths = Logger.genpaths(logname)
        confdir = paths["confdir"]
        # Check to make sure that user implemented a real directory name
        if os.path.isdir(confdir + logname):
            return True
        else:
            return False

    def mklogtemplate(self, logname, settings):
        """Make a new log template in the .loggers directory."""
        paths = Logger.genpaths(logname)
        os.mkdir(paths["logdir"])
        log.confinit(logname, settings)
        return True

    def confinit(self, logger, settings):
        paths = self.genpaths(logger)
        confpath = paths["confpath"]
        config = open(confpath, 'w')
        json.dump(settings, config)
        config.close()

    def search_column(self, column_data, searchterm, field):
        """Search the column with the regex searchterm using the fields search 
        function or a fallback."""
        if "search" in field.scripts.keys():
            search_results = field.search(searchterm, column_data)
            return search_results
        else:
            try:
                pattern = re.compile(searchterm)
            except:
                return 'regex_compile_error'
            search_results = []
            for index in range(0, len(column_data)):
                item = column_data[index]
                if pattern.search(item):
                    search_results.append((index, item))
            return search_results

    def verify_file_before_write(self, filepath):
        """Verify that a file does not already exist and is not a directory
        and that the path to new file is writable."""
        pathsplit = os.path.split(filepath)
        if pathsplit[1] == '':
            return 'filepath_was_directory'
        elif not os.path.isdir(pathsplit[0]):
            return 'invalid_filepath'
        elif os.path.isfile(filepath):
            yes = input(filepath + "already exists, overwrite? Y/N:")
            if yes == 'yes' or yes == 'y':
                pass
            else:
                return 'existed_no_overwrite'
        else:
            return True

    def descend_directory(self, directory, export_archive):
        """Descend a directory recursively, adding items to zip archive."""
        if os.path.isdir(directory):
            files2backup = os.listdir(directory)
            for _file in files2backup:
                file2backup = os.path.join(directory, _file)
                if os.path.isdir(file2backup):
                    self.descend_directory(file2backup)
                else:
                    export_archive.write(file2backup, _file)
        else:
            raise ValueError("Function descend_directory in export recieved"
                                 " a file as argument.")
        return export_archive

    def export(self, logname, filepath):
        """Export a log as a zipfile to filepath."""
        pathcheck = self.verify_file_before_write(filepath)
        if pathcheck is not True:
            return pathcheck
        else:
            paths = Logger.genpaths(Logger, logname)
            logdir = paths["logdir"]
            export = zipfile.ZipFile(filepath, "w")
            if os.path.isdir(logdir):
                export_archive = self.descend_directory(logdir, export)
                export_archive.close()
                return True
            else:
                return "log_does_not_exist"

    def export_all(self, filepath):
        """Export every log and all settings and directories to filepath."""
        pathcheck = self.verify_file_before_write(filepath)
        if pathcheck is not True:
            return pathcheck
        else:
            paths = Logger.genpaths(Logger, "placeholder")
            confdir = paths["confdir"]
            export = zipfile.ZipFile(filepath)
            export_archive = self.descend_directory(confdir, export)
            export_archive.close()
            return True

    def export_direct(self, data, filepath):
        """Export the objects in data to zipped json archive at filepath."""
        pathcheck = self.verify_file_before_write(filepath)
        if pathcheck is not True:
            return pathcheck
        else:
            export_archive = zipfile.ZipFile(filepath, "w")
            data_json = json.dumps(data)
            export_archive.writestr("data.json", data_json)
            export_archive.close()
            return True

    def export_entries(self, logname, entries, fields, filepath):
        """Export the entries of logname given by the list of ranges <entries>
        to filepath."""
        pathcheck = self.verify_file_before_write(filepath)
        if pathcheck is not True:
            return pathcheck
        else:
            log_entries = self.load_log_entries(logname, entries, fields)
            export_archive = zipfile.ZipFile(filepath, "w")
            entries_json = json.dumps(log_entries)
            export_archive.writestr("entries.json", entries_json)
            export_archive.close()
            return True
        

class LogPrinter():
    """Genlog implements a dynamic log printing system that gives execution 
    hooks to style output and control line wrapping. Each column declares a
    minimum and maximum width, which works within the context of the log itself
    declaring a minimum and maximum width for each line of the output. 

    Each minimum and maximum is either *fixed* or *dynamic*. Dynamic columns
    can be trimmed to fit the requirements of the log output, fixed columns
    *must* be printed with their full width on each line. Fixed columns are
    dangerous because if they exceed the fixed properties of the log you get an
    error so dynamic columns are always preferred where possible. 

    With columns fixed and dynamic control what happens when line wrapping is 
    forced by the output. In logs it controls what is allowable output and how 
    much space columns have to work with.

    The exact behavior of each is as follows:

    For logs:

    Fixed Minimum:
        Each line *must* be at least as many characters as the minimum defined.

    Fixed Maximum:
        Each line *must* be no more than as many characters as the maximum 
        defined.
    
    Dynamic Minimum:
        The printer will try to optimize the widths of columns so that each line
        is at least this many characters long. But it won't gauruntee it.

    Dynamic Maximum:
        The printer will try to optimize the widths of columns so that each line
        is no more than this many characters, but it won't guauruntee it.

    For columns:

    Fixed Maximum:
        The printer *must* give the column this much space for line wrapping.

    Fixed Minimum:
        The printer *must* give the column this much space for line wrapping.
        Only taken into account when the column has a dynamic maximum.

    Dynamic Maximum:
        The printer will try to optimize the widths of columns so that
        this field will have its ideal line wrapping width. But it's not 
        guarunteed.

    Dynamic Minimum:
        The printer will try to optimize the widths of columns so that 
        this field will have at least this much line wrapping width. But it's
        not guarunteed.

    Printer objects are composed from two base objects, a Minimum and a Maximum
    which have their dynamicism as object attributes along with a width. Each 
    column has an execution hook that takes the data in the column and has full
    access to pythons programming facilities to manipulate and style the data.
    Each log has an execution hook that takes each row in the log after it's been
    styled by the execution hooks for each column and returns styling applied 
    across the entire row, with control of seperators and the header and footer
    of the log file.

    The process for determining how much space each column gets is as follows:

    Fixed width columns are allotted the necessary space from what is available.
    Since fixed maximums demand that a certain amount of space be *available*
    they are considered first and their minimums ignored. If these exceed the
    fixed parameters of the PrintLog object then an error is raised. Next the
    fixed minimums are considered for those fields which have a dynamic maximum.
    If these combined with the fixed maximums exceed the fixed parameters of the
    log an error is raised. 

    Finally dynamic column widths are considered. For dynamic columns
    the amount of space left is evaluated and if sufficient all dynamic columns
    are granted their maximum line wrapping width. Otherwise the smallest column
    width is used to determine a ratio between the columns that will be used to
    trim their lengths down from their dynamic maximums. When a column reaches
    it's minimum dynamic or otherwise then trimming other dynamic maximums down
    to their minimum will take priority over trimming past the dynamic minimum.

    Only once all other resources have been exhausted will the printer start
    trimming widths past their dynamic minimums to save space.

    Dealing with unbounded maximums:
    As fixed maximums are allowed to declare an unbounded amount of space using 
    the '*', if this is the case then all dynamic columns are reduced to their 
    minimum fixed or otherwise and more will be trimmed in the case of conflicts.

    Dynamic maximums that declare an unbounded amount of space are given as much
    space as it is possible to give within the constraint that it will not bring
    column widths down past their minimum dynamic or otherwise.

    If multiple columns declare unbounded widths then the space will be divided
    equally among them.
    """
    class AbstractWidth():
        """Base class for minimum and maximum widths for columns."""
        def __init__(self, column, width, width_type='dynamic'):
            if width_type not in ('dynamic', 'fixed'):
                raise ValueError("Width type" + width_type + "not a valid type.")
            elif not isinstance(width, int):
                raise ValueError("Width must be of type int, got '" + 
                                 str(type(width)) + "'.")
            elif width < 1:
                raise ValueError("Width must be at least one.")
            else:
                self.width = width
                self.width_type = width_type
                self.column = column

    class Minimum(AbstractWidth):
        """Set the minimum width of a column in the text output.
        Valid values for width_type are 'dynamic' and 'fixed'.
        """
        pass

    class Maximum(AbstractWidth):
        """Set the maximum width of a column in the text output.
        Valid values for width_type are 'dynamic' and 'fixed'.
        """
        pass

    class AbstractPrint():
        """Base class for print objects such as logs and columns."""
        def __init__(self, minimum, maximum):
            if minimum.width > maximum.width:
                raise ValueError("Minimum was greater than Maximum.")
            self.minimum = minimum
            self.maximum = maximum

    class PrintLog(AbstractPrint):
        'Defines the line wrapping width and dimensions of a log output medium.'
        def __init__(self, minimum, maximum):
            super().__init__(self, minimum, maximum)
            self.fixed_column_spacing = {}
            self.dynamic_column_spacing = {}
            self.seperator = None

        def _print_debug(self, pcolumn_widths):
            """Print debugging info for someone to figure out what fixed columns
            caused an error."""
            erronous_pcolumns = {}
            for pcolumn in pcolumns:
                fname = pcolumn.column["fname"]
                
        def set_seperator(self, seperator):
            self.seperator = str(seperator)

        def add_fixed_spacing(self, pcolumns):
            """Add and check the space declaration to the print objects internal 
            tracker.

            For each given print column, the print medium checks that it plus 
            the previous print columns does not overflow the constraints of what 
            is allowable in the print medium. since a print column can be in the 
            fixed category for a minimum or a maximum the print medium also has 
            to remember which the space allocation was based off of.
            """
            for pcolumn in pcolumns:
                if pcolumn.maxium.width_type == 'fixed':
                    basis = pcolumn.maximum
                    allocation = pcolumn.maximum.width
                    self.fixed_column_spacing[pcolumn] = {"basis":basis, 
                                                          "allocation":allocation}
                else:
                    return False
                fixed_max_widths = {}
                for space_allocation in self.fixed_column_spacing:
                    allocation_dict = fixed_column_spacing[space_allocation]
                    if ((space_allocation.maximum is 
                         allocation_dict["basis"]) and 
                         space_allocation.maximum.width != '*'):
                        fname = space_allocation.column["fname"]
                        allocation = allocation_dict["allocation"]
                        fixed_max_widths[fname] = allocation
                    else:
                        raise ValueError("Supposed to have fixed basis but didn't"
                                         " pass relevant tests.")
                sep_len = ColumnTrimmer.calculate_seperator_len(ColumnTrimmer, 
                                                                self.seperator,
                                                                pcolumns)
                if sum(fixed_max_widths.values()) > self.maximum.width:
                    pprint.pprint(fixed_max_widths)
                    raise ValueError("Length of fixed maximums exceeded constraints"
                                     " of print medium.")
                elif sum(fixed_max_widths.values()) + sep_len > self.maximum.width:
                    pprint.pprint(fixed_max_widths)
                    print("Seperator lengths:", str(sep_len))
                    raise ValueError("Length of fixed maximums and seperators"
                                     " exceeded constraints of print medium.")
                elif (sum(fixed_max_widths.values()) + sep_len + len(pcolumns)
                      > self.maximum.width):
                    pprint.pprint(fixed_max_widths.values())
                    print("Seperator lengths:", str(sep_len))
                    print("Number of columns:", str(len(pcolumns)))
                    raise ValueError("Length of fixed maximums and seperators"
                                     " and minimum single character for each"
                                     " column exceeded constraints of print"
                                     " medium.")
                else:
                    return True

        def add_dynamic_spacing(self, pcolumns):
            """Add the space declarations to the print objects internal
            tracker.

            Calculates the remaining space leftover after the fixed columns are
            accounted for. Importantly fixed minimums do not count as taking up
            space because their dynamic maximums must have equal or more space
            so to count them would misrepresent how much space is remaining.
            """
            dynamic_buffer = {}
            for pcolumn in pcolumns:
                maximum = pcolumn.maximum.width_type
                minimum = pcolumn.minimum.width_type
                max_width = pcolumn.maximum.width
                if maximum == 'dynamic' and minimum == 'dynamic':
                    pcolumn_buffer[pcolumn] = {"minimum_type":'dynamic',
                                               "allocation":max_width}
                elif maximum == 'dynamic' and minimum == 'fixed':
                    pcolumn_buffer[pcolumn] = {"minimum_type":'fixed',
                                               "allocation":max_width}
            fixed_max_widths = []
            for space_allocation in self.fixed_column_spacing:
                basis = self.fixed_column_spacing[space_allocation]["basis"]
                if space_allocation.maximum is basis:
                    allocation = (self.fixed_column_spacing
                                  [space_allocation]["allocation"])
                    fixed_max_widths.append(allocation)
            sep_len = ColumnTrimmer.calculate_seperator_len(ColumnTrimmer,
                                                            self.seperator,
                                                            pcolumns)
            remaining_space = ((self.maximum.width - sum(fixed_max_widths)) 
                               - sep_len)
            dynamic_spacing = []
            for pcolumn in pcolumn_buffer:
                dynamic_spacing.append(pcolumn_buffer[pcolumn]["allocation"])
            if sum(dynamic_spacing) > remaining_space:
                trimmed_columns = self.trim_space(dynamic_buffer, remaining_space)
                columns = {}
                for column in trimmed_columns:
                    pcolumn = column[0]
                    allocation = column[1]
                    columns[pcolumn] = {"allocation":allocation}
            elif sum(dynamic_spacing) <= remaining_space:
                columns = dynamic_buffer
            self.dynamic_column_spacing = columns
            return True

        def reorder_columns(self, fields):
            """After all space allocations have been added to the internal 
            tracker make final preperations for printing.
            """
            column_fnames = {}
            for pcolumn in self.fixed_column_spacing:
                fname = pcolumn.column["fname"]
                allocation = self.fixed_column_spacing[pcolumn]["allocation"]
                column_fnames[fname] = (pcolumn, allocation)
            for pcolumn in self.dynamic_column_spacing:
                fname = pcolumn.column["fname"]
                allocation = self.dynamic_column_spacing[pcolumn]["allocation"]
                column_fnames[fname] = (pcolumn, allocation)
            print_columns = []
            for field in fields:
                fname = field["fname"]
                print_columns.append(column_fnames[fname])
            return print_columns

    class ColumnTrimmer():
        """Trim columns down to their proper sizing for space allocation and
        printing."""
        def calculate_seperator_len(self, seperator, columns):
            """Calculate the length of the seperators given the seperator as a
            string and its columns."""
            if seperator:
                seperators = len(columns) - 1
                seperator_length = len(seperator)
                return seperators * seperator_length
            else:
                return 0

        def trim_column(self, column, smallest, slack, remaining_space):
            """Trim the length of a single column."""
            current = column[1]
            ratio_step = (current - (current % smallest)) / smallest
            if slack is 0:
                 return column
            elif slack % ratio_step == 0:
                trimmed_allocation = column_allocation - ratio_step
                return (column[0], trimmed_allocation)
            elif slack % ratio_step > 0:
                slack_difference = slack % ratio_step
                trimmed_allocation = column_allocation - slack_difference
                return (column[0], trimmed_allocation)
            else:
                raise ValueError("Somehow trim_column got a slack outside"
                                 " it's assumed operating parameters.")

        def trim_maximums(self, dynamic_buffer, remaining_space):
            """Trim dynamic maximums until they're either below the maximum of the
            print medium or all equivalent to the print columns minimum."""
            pcolumn_allocations = []
            for pcolumn in dynamic_buffer:
                allocation = dynamic_buffer[pcolumn]["allocation"]
                pcolumn_allocations.append((pcolumn, allocation))
            pcolumn_allocations.sort(key=(lambda allo: allo[1]))
            smallest = pcolumn_allocations[0]
            trimmed_columns = pcolumn_allocations[:]
            trimmed_columns.reverse()
            stop = False
            while stop is False:
                for index in range(0, len(trimmed_columns)):
                    column = trimmed_columns.pop(index)
                    column_allocation = column[1]
                    min_width = column[0].minimum.width
                    slack = column_allocation - min_width
                    column = self.trim_column(column, smallest, slack, 
                                              remaining_space)
                    trimmed_columns.append(column)
                    allocation_buffer = []
                    minimums = []
                    for trim_column in trimmed_columns:
                        minimums.append(trim_column[0].minimum.width)
                        allocation_buffer.append(trim_column[1])
                    if sum(allocation_buffer) <= remaining_space:
                        return (trimmed_columns, True)
                    elif sum(allocation_buffer) == sum(minimums):
                        return (trimmed_columns, False)
                    else:
                        pass

        def trim_minimums(self, dynamic_buffer, trimmed_columns, remaining_space):
            """Trim a set of dynamic minimums after they've already been trimmed
            as dynamic maximums.

            trimmed_columns: The already-trimmed columns to trim even further.

            remaining_space: The amount of space remaining after fixed maximums
            and seperators have been taken into account."""
            dynamic_minimums = []
            fixed_minimums = []
            for index in range(0, len(trimmed_columns)):
                pcolumn = trimmed_columns[index][0]
                minimum_type = dynamic_buffer[pcolumn]["minumum_type"]
                if minumum_type == 'dynamic':
                    dynamic_minimums.append((pcolumn, pcolumn.minimum.width))
                    trimmed_columns.pop(index)
                elif minimum_type == 'fixed':
                    fixed_minimums.append(pcolumn.minimum.width)
                else:
                    raise ValueError("minimum_type was neither fixed or dynamic.")
            if sum(fixed_minimums) > remaining_space:
                raise ValueError("Length of fixed minimums exceeded remaining"
                                 " space.")
            elif sum(fixed_minimums) and dynamic_minimums > remaining_space:
                raise ValueError("Length of fixed minimums left no room for"
                                 " dynamic columns.")
            else:
                pass
            dynamic_minimums.sort(key=(lambda allo: allo[1]))
            smallest = dynamic_minimums[0]
            dynamic_minimums.reverse()
            stop = False
            while stop is False:
                for index in range(0, len(dynamic_minimums)):
                    column = dynamic_minimums.pop(index)
                    minimum_allocation = column[1]
                    slack = minimum_allocation - 1
                    column = self.trim_column(column, smallest, slack, 
                                              remaining_space)
                    dynamic_minimums.append(column)
                    trimmed_allocations = []
                    minimum_allocations = []
                    for column in trimmed_columns:
                        allocation = column[1]
                        trimmed_allocations.append(allocation)
                    for column in dynamic_minimums:
                        allocation = column[1]
                        minimum_allocations.append(allocation)
                    if (sum(trimmed_allocations) + sum(minimum_allocations) 
                        <= remaining_space):
                        return trimmed_columns + dynamic_minimums
                    else:
                        pass


        def trim_space(self, dynamic_buffer, remaining_space):
            """If there is not enough room to give every column its dynamic
            maximum, trim space until there is or raise error.

            Dynamic minimums are absolutely prioritized over dynamic maximums.
            What this means is that if it comes down to a choice between 
            shortening a dynamic minimum and shortening a dynamic maximum the
            maximum will always be shortened.

            dynamic buffer: A dictionary of dynamic print columns under 
            consideration.

            remaining space: The amount of remaining space left in the print
            medium.
            """ 
            trimmed_columns_tuple = self.trim_maximums(dynamic_buffer, 
                                                       remaining_space)
            trimmed_columns = trimmed_columns_tuple[0]
            if trimmed_columns_tuple[1] is False:
                trimmed_min_columns = self.trim_minimums(dynamic_buffer,
                                                         trimmed_columns,
                                                         remaining_space)
                return trimmed_min_columns
            else:
                return trimmed_columns
           

            
    class PrintColumn(AbstractPrint):
        'Defines the line wrapping width of a single column to be printed.'
        def __init__(self, minimum, maximum, column):
            super().__init__(self, minimum, maximum)
            self.column = column

    class OutputFormat():
        """Template class for an oformat module. 
        """
        def spacing(self, column, column_formats, print_object, known={}):
            """A stub to be filled in by a real function.

            Should return a PrintColumn object.
            """
            pass

        def format(self, column, width):
            """A stub to be filled in by a real function."""
            pass

    def print_to(self, log, print_object, logname):
        """Print a log object given as JSON and return text formatted according
        to the properties of the given print object."""
        #routine to grab the oformat scripts and etc for each column
        settings = Logger.readconf(Logger, logname)
        log_oformat = Logger.getscript(Logger, settings["formatting"], logname)
        seperator = log_oformat.seperator
        fields = Logger.getfields(Logger, settings, logname)
        fields_dict = {}
        for field in fields:
            fields_dict[field["fname"]] = field
        column_formats = []
        for column in log:
            fname = column["fname"]
            column_field = fields_dict[fname]
            oformat = column_field.oformat
            column_formats.append((column, oformat))
        declarations = self.spacing_negotiation(column_formats, print_object)
        print_medium = self.determine_widths(declarations, print_object, seperator)
        print_columns = print_medium.reorder_columns(fields)
        formatted_output = self.print_log(print_columns, column_formats, log_oformat)
        return formatted_output

    def spacing_negotiation(self, column_formats, print_object):
        """Call the spacing declaration method of each oformat script module.
        Each call is passed the other oformat modules and the print_object to
        prepare spacing for. The first step of the log printing process is to
        figure out the space allocated to each column to print in, each call
        ultimately returns a PrintColumn object that is evaluated by the Printer
        to determine final widths for each column. 

        Since the PrintColumn returned might depend on what the other columns
        declare it is possible that a oformat spacing negotiation method might
        run the spacing negotiation methods of the other columns with the same
        information it recieved when it was called along with its desired width
        to see what that means the other columns will declare and adjust its own
        width accordingly.

        column_formats: A list of tuples where each tuple is a pair with
        a column on the left and its oformat module on the right.

        print_object: The print medium to prepare spacing for.
        """
        column_widths = []
        for column in column_formats: 
            declaration = oformat.spacing(column, column_formats, print_object)
            column_widths.append(declaration)
        return column_widths

    def determine_widths(self, column_widths, print_object, seperator):
        """Given the spacing declarations of each column and the dimensions of
        the print medium, determine how much space each column will actually get 
        to print in.
        """
        print_object.set_seperator(seperator)
        print_object.add_fixed_spacing(column_widths)
        print_object.add_dynamic_spacing(column_widths)
        return print_object

    def print_log(self, print_columns, column_formats, log_oformat):
        """Print a log given as print columns and a log oformat."""
        formatted_columns = []
        for index in range(0, len(print_columns)):
            pcolumn = print_columns[index]
            pcolumn_fname = pcolumn.column["fname"]
            column = column_formats[index][0]
            oformat_fname = column["fname"]
            oformat = column_formats[index][1]
            seperator = log_oformat.seperator
            if pcolumn_fname == oformat_fname:
                formatted_data = oformat.format(column, pcolumn, seperator)
                formatted_columns.append({"fname":column["fname"],
                                          "olabel":column["olabel"],
                                          "data":formatted_data})
            else:
                raise Exception("Data corruption detected in print_log.")
        formatted_output = log_oformat.format(formatted_columns)
        return formatted_output
            


class Field():
    """Implements the base field object for the generic logger."""
    def __init__(self, logname=None, name=None, flabel=None, 
                 olabel=None, ftype=None, prompt=None,
                 restrictions=None, onmatch=None, handlers=None, 
                 oformat=None, search=None):
        self.logname = logname
        self.name = name
        self.flabel = flabel
        self.olabel = olabel
        self.ftype = ftype
        self.prompt = prompt
        self.restrictions = restrictions
        self.onmatch = onmatch
        self.handlers = handlers
        self.oformat = oformat
        self.search = search
    
    def validate(self, line):
        """Validate a line of input according to field restrictions."""
        criteria = Restriction(self.restrictions, self.onmatch)
        if criteria.validate(line):
            return True
        else:
            return False

    def field_dict(self, fdict_template):
        """Return a flat dictionary of the field objects attributes. Given a 
        dictionary with keys that correspond to the name of the attributes you 
        want from the field object fills in the values and returns the dictionary.
        """
        if "type" in fdict_template.keys():
            fdict_template["type"] = self.ftype
        for attribute in fdict_template:
            try:
                fdict_template[attribute] = getattr(self, attribute)
            except AttributeError:
                raise ValueError("field_dict tried to access an attribute that"
                                 " was not part of field object.")
        return fdict_template

    def from_fdict(self, fdict):
        """Return a field object from a flat field dictionary."""
        new_fobject = Field()
        for key in fdict:
            try:
                setattr(new_fobject, key, fdict[key])
            except TypeError:
                raise TypeError("from_fdict recieved dictionary with key that"
                                " was of type other than string.")
        return new_fobject
            
    def get_script(self, script, logname):
        return Logger.get_script(Logger, script, logname)
        
    def unpack_scripts(self, 
                       scripts=None,
                       logname=None):
        """Unpack given scripts and assign them as methods of field object."""
        if not scripts:
            scripts = self.scripts
        if not logname:
            logname = self.logname
        for scriptkey in scriptnames:
            scriptname = scriptnames[scriptkey]
            if scriptname:
                script = self.get_script(scriptname, logname)
            else:
                setattr(self, (scriptkey + "_main"), None)
            setattr(self, (scriptkey + "_main"), script)
        return True


class Restriction():
    """Bundle together a regex restriction, whether input should be discarded on
    match or on None."""
    def __init__(self, regex, onmatch):
        self.regex = regex
        self.onmatch = onmatch
    
    def validate(line):
        """Validate a line of input by matching it against the regex."""
        if self.regex == None:
            return True
        restrictions = re.compile(self.regex)
        match = restrictions.search(line)
        if match and self.onmatch == 'keep':
            return True
        elif not match and self.onmatch == 'discard':
            return True
        else:
            return False
