#!/usr/bin/env python3

# Check for the right Python version
import sys
if sys.version_info[0] < 3:
	raise Exception("Lexipython requires Python 3")

import argparse
import os
import re
import json
import src.utils as utils

def is_lexicon(name):
	"""
	Checks whether the given folder is a Lexicon game.
	Inputs:
		name    The Lexicon name to check. Assumed to be an existing folder.
	Output:
		Returns a tuple (result, msg, status), where result is True if the
		given name is a Lexicon game and False otherwise, msg is the Lexicon's
		status or an error message, and status is the status dictionary of the
		Lexicon or None.
	"""
	if not os.path.isfile(os.path.join("lexicon", name, "lexicon.cfg")):
		return (False, "'{}' is not a Lexicon game, or its config file may be missing.".format(name), None)
	if not os.path.isfile(os.path.join("lexicon", name, "status")):
		return (True, "status missing", None)
	with open(os.path.join("lexicon", name, "status")) as statusfile:
		raw = statusfile.read()
		if len(raw) == 0:
			return (True, "unbuilt", {})
		try:
			status = json.loads(raw)
		except:
			return (True, "status corrupted", None)
		return (True, "ye", status) # TODO
	return (False, "Error checking Lexicon status", None)

def overview_all():
	"""
	Prints the names and statuses of all extant Lexicons,
	or a short help message if none have been created yet.
	"""
	# Scan the directory
	lexicon_names = []
	with os.scandir("lexicon") as lexicons:
		for entry in lexicons:
			if entry.is_dir():
				result, msg, status = is_lexicon(entry.name)
				if result:
					lexicon_names.append((entry.name, msg))
	# Print the results
	if len(lexicon_names) > 0:
		l = max([len(name) for name, msg in lexicon_names]) + 4
		print("Lexicons:")
		for name, msg in sorted(lexicon_names):
			print("  {}{}{}".format(name, " " * (l - len(name)), msg))
	else:
		print("There are no Lexicons yet. Create one with:\n\n"\
		      "    lexipython.py [name] init")

def overview_one(name):
	"""
	Prints the status and summary information for the Lexicon with the
	given name.
	"""
	# Verify the name
	if not os.path.isdir(os.path.join("lexicon", name)):
		print("Error: There is no Lexicon named '{}'.".format(name))
		return
	result, msg, status = is_lexicon(name)
	if not result:
		print("Error: " + msg)
		return
	# Print status and summary
	print(msg)
	print(status)
	# TODO

def run_command(name, command):
	"""
	Runs a command on a Lexicon.
	"""
	if command == "init":
		# Check that the folder isn't already there
		if os.path.exists(os.path.join("lexicon", name)):
			print("Error: Can't create '{}', it already exists.".format(name))
			return
		# Create the Lexicon
		command_init(name)
		return
	elif command == "build":
		if not os.path.exists(os.path.join("lexicon", name)):
			print("Error: There is no Lexicon named '{}'.".format(name))
			return
		result, msg, status = is_lexicon(name)
		if not result:
			print("Error: " + msg)
			return
		# Build the Lexicon
		command_build(name)
		return
	elif command == "run":
		if not os.path.exists(os.path.join("lexicon", name)):
			print("Error: There is no Lexicon named '{}'.".format(name))
			return
		result, msg, status = is_lexicon(name)
		if not result:
			print("Error: " + msg)
			return
		# Run a server managing the Lexicon
		command_run(name)
		return
	else:
		print("Error: '{}' is not a valid command.".format(command))
		return

def command_init(name):
	"""
	Sets up a Lexicon game with the given name.
	"""
	# Create the folder structure
	lex_path = os.path.join("lexicon", name)
	os.mkdir(lex_path)
	os.mkdir(os.path.join(lex_path, "src"))
	os.mkdir(os.path.join(lex_path, "article"))
	os.mkdir(os.path.join(lex_path, "contents"))
	os.mkdir(os.path.join(lex_path, "formatting"))
	os.mkdir(os.path.join(lex_path, "rules"))
	os.mkdir(os.path.join(lex_path, "session"))
	os.mkdir(os.path.join(lex_path, "statistics"))
	# Open the default config file
	config = utils.load_resource("lexicon.cfg")
	# Edit the name field
	config = re.sub("Lexicon Title", "Lexicon {}".format(name), config)
	# Create the Lexicon's config file
	with open(os.path.join(lex_path, "lexicon.cfg"), "w") as config_file:
		config_file.write(config)
	# Create an example page
	with open(os.path.join(lex_path, "src", "example-page.txt"), "w") as destfile:
		destfile.write(utils.load_resource("example-page.txt"))
	# Create an empty status file
	open(os.path.join(lex_path, "status"), "w").close()
	print("Created Lexicon {}".format(name))

def command_build(name):
	"""
	Rebuilds the browsable pages of a Lexicon.
	"""
	pass

def command_run(name):
	"""
	Runs as a server managing a Lexicon.
	"""
	pass

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