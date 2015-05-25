import argparse

from logger import Logger, LogPrinter, Restriction

import cli_interface

def main():
    """Handle command line arguments, determine which interface to use and cede
    control to it."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--interface",default='cli',help="Specify which"
                        " interface to use. Valid options: cli")
    parser.add_argument("-l", "--logger", help="Choose which logger to use."
                        " When standalone skip straight to the logmenu for that"
                        " log.")
    parser.add_argument("--entry", help="Seed a new entry from the command line."
                        " Takes the values that should go in each field column"
                        " in the logical order and adds them as a new entry to"
                        " the log given as -l. First argument should be syntax"
                        " the name of the log to append entry to, if updating"
                        " a previous entry the entry should be specified with"
                        " a colon. Example: worklog:457 Each value should be a"
                        " key value pair specified in the same way. Example:"
                        " time_started:1000, time_ended:1500 Values should be"
                        " comma seperated. For longer values or ones that"
                        " include commas quotation marks can be used around the"
                        " value. If the value includes quotation marks they can"
                        " be escaped using backslashes with pythons escape"
                        " syntax.")
    parser.add_argument("-p","--print", help="Print a log entry specified"
                        " according to the syntax logname:entry_id. For example:"
                        " worklog:457")
    args = parser.parse_args()
    if args.interface != 'cli':
        raise NotImplementedError("Only cli interface available at this time."
                                  " Check back for updates to this program.")
    if args.logger:
        logname = str(args.logger)
        LogMenu = cli_interface.CliLogMenu(logname)
        LogMenue.cmdloop()
    if args.entry:
        raise NotImplementedError("Manual additions of entries not available at"
                                  " this time. (But rest assured will be used"
                                  " to implement a web interface.) Check back"
                                  " for updates to this program.")
    if args.print:
        raise NotImplementedError("The program isn't complete yet. Sorry.")
    if not args.entry and not args.print and not args.logger:
        MainMenu = cli_interface.CliMainMenu()
        MainMenu.cmdloop()
    return True

main()
