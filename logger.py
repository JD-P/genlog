#!/usr/bin/python3

# We start by importing time and datetime. The former lets us get and write the current time and date to a file. The latter lets us get the distance between two times

import time,datetime

# We import json so that we can put both the machine readable version and the version formatted for human consumption in seperate files.

import json

# We import os so that we can make the config file if it doesn't already exist, and check for its existence.

import os

# We import string for input validation

import string

# We import argparse to handle command line arguments.

import argparse

import cmd

import re

import importlib

import zipfile

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
        

    def main(self):
        """Handle command line arguments, determine which interface to use and cede control to it."""
        parser = argparse.ArgumentParser()
        parser.add_argument("-p","--print",default=False,help='Print the text log to standard output.')
        parser.add_argument("-i","--interface",default='cli',help='Specify which interface to use. Valid options: cli')
        args = parser.parse_args()
        if args.print:
            self.tlogprint(args.print)
            return 0
        elif args.interface == 'cli':
            global log
            log = Logger(CliInterface())
            CliInterface.cli_main()
        elif args.interface == 'gui':
            print("No GUI interface available at this time.")
        else:
            raise ValueError("Interface somehow not present.")

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
            raise ValueError(("No script by name " + script + "in local or global")
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
    """Print the log in text format(s)."""
    def tlogwrt(self, entry,log):
        """Take an entry dictionary and write out to the human readable log based on it."""
        # Check if textlog file exists, if not write instead of append
        tlog = open(log,'a')
        tlog.write("----\n")
        for lvalue in entry:
            olabel = str(entry.get(lvalue)[1])
            value = str(entry.get(lvalue)[0])
            tlog.write(olabel + " " + value + "\n\n")
        tlog.write("----\n\n")

    def tlogprint(self, entry, log):
        """Take the JSON log and print a formatted version to standard output."""
        jlog = open(log, 'r')

    def printentry(self, entry, formatting):
        """Take a given entry and return a formatted version."""
        for field in entry:
            olabel = formatting.get("olabel")
            ftag = formatting.get("oformat")
            print()


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
                       scripts=self.scripts,
                       logname=self.logname):
        """Unpack given scripts and assign them as methods of field object."""
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
        if self.regex = None:
            return True
        restrictions = re.compile(self.regex)
        match = restrictions.search(line)
        if match and self.onmatch == 'keep':
            return True
        elif not match and self.onmatch == 'discard':
            return True
        else:
            return False

Logger.main()
