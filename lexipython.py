#!/usr/bin/env python3

# Check for the right Python version
import sys
if sys.version_info[0] < 3:
	raise Exception("Lexipython requires Python 3")

import argparse
import os

def is_lexicon(name):
	"""
	Checks whether the given name is an extant Lexicon game.
	Inputs:
		name    The Lexicon name to check.
	Output:
		If the given name is an extant Lexicon, returns a tuple (True, status)
		where status is a string with the status of the named Lexicon.
		If the given name is not an extant Lexicon, returns a tuple
		(False, errormsg) where errormsg is a string detailing the error.
	"""
	if not os.path.isdir(os.path.join("lexicon", name)):
		return (False, "There is no Lexicon named '{}'.".format(name))
	# TODO: Verify the folder is a Lexicon
		#return (False, "'{}' is not a Lexicon game, or it may be corrupted.".format(name))
	return (True, "A Lexicon")

def overview_all():
	"""
	Prints the names and statuses of all extant Lexicons,
	or a short help message if none have been created yet.
	"""
	# Scan the directory
	lexicon_names = []
	with os.scandir("lexicon") as lexicons:
		for entry in lexicons:
			check = is_lexicon(entry.name)
			if check[0]:
				lexicon_names.append((entry.name, check[1]))
	# Print the results
	if len(lexicon_names) > 0:
		l = max([len(name[0]) for name in lexicon_names]) + 4
		print("Lexicons:")
		for name, status in sorted(lexicon_names):
			print("  {}{}{}".format(name, " " * (l - len(name)), status))
	else:
		print("There are no Lexicons yet. Create one with:\n\n"\
		      "    lexipython.py [name] init")

def overview_one(name):
	"""
	Prints the status and summary information for the Lexicon with the
	given name.
	"""
	# Verify the name
	check = is_lexicon(name)
	if not check[0]:
		print("Error: " + check[1])

def run_command(name, command):
	"""
	Runs the specified command on the specified Lexicon.
	"""
	# Verify name
	check = is_lexicon(name)
	if not check[0]:
		print("Error: " + check[1])
		return
	# Dispatch commands
	if command == "init":
		return
	elif command == "build":
		return
	elif command == "run":
		return
	else:
		print("Error: '{}' is not a valid command.".format(command))
		return

def main():
	parser = argparse.ArgumentParser(
		description="Lexipython is a Python application for playing the Lexicon RPG.",
		epilog="Run lexipython.py without arguments to list the extant Lexicons.\n\n"\
		       "Available commands:\n\n"\
		       "    init        Create a Lexicon with the provided name\n"\
		       "    build       Build the Lexicon, then exit\n"\
		       "    run         Launch a persistent server managing the Lexicon\n",
		formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument("name", help="The name of the Lexicon to operate on",
		nargs="?", default=None)
	parser.add_argument("command", help="The operation to perform on the Lexicon",
		nargs="?", default=None)
	args = parser.parse_args()
	
	# If no Lexicon as specified
	if args.name is None:
		overview_all()
	# If no command was specified
	elif args.command is None:
		overview_one(args.name)
	# A command was specified
	else:
		run_command(args.name, args.command)

if __name__ == "__main__":
	main()