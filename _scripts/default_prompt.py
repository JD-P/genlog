import unittest

class Test(unittest.TestCase):
    def test_cli(self):
        """Test that the cli interface works."""
        self.assertTrue('cli' in Prompts.interfaces)
        self.assertTrue(Prompts.cli_prompt)

def main(interface, flabel):
    """The default prompt, which accepts a single line of text and returns a 
    dictionary. The dictionary can have many key:value pairs but the one expected
    is 'line' which is the actual string to be entered into the row."""
    vdict = {}
    if interface == 'cli':
        vdict["line"] = Prompts.cli_prompt(flabel)
        return vdict
    else:
        raise ValueError("Interface requested is not supported by this field.")

class Prompts():
    interfaces = ['cli']
    """Implements the actual prompt widgets for each interface."""
    def cli_prompt(flabel):
        """Prints a line of text given with flabel and otherwise uses pythons
        line input function to get a piece of text from the user."""
        line = input(flabel)
        return line
