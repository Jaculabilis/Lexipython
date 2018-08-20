import os
import re
from urllib import parse

# Short utility functions for handling titles

def titlecase(s):
	"""
	Capitalizes the first word.
	"""
	s = s.strip()
	return s[:1].capitalize() + s[1:]

def titleescape(s):
	"""
	Makes an article title filename-safe.
	"""
	s = s.strip()
	s = re.sub(r"\s+", '_', s)  # Replace whitespace with _
	s = parse.quote(s)          # Encode all other characters
	s = re.sub(r"%", "", s)     # Strip encoding %s
	if len(s) > 64:             # If the result is unreasonably long,
		s = hex(abs(hash(s)))[2:]  # Replace it with a hex hash
	return s

def titlesort(s):
	"""
	Reduces titles down for sorting.
	"""
	s = s.lower()
	if s.startswith("the "): return s[4:]
	if s.startswith("an "): return s[3:]
	if s.startswith("a "): return s[2:]
	return s

# Load functions

def load_resource(filename, cache={}):
	"""Loads files from the resources directory with caching."""
	if filename not in cache:
		with open(os.path.join("src", "resources", filename), "r", encoding="utf-8") as f:
			cache[filename] = f.read()
	return cache[filename]

def load_config(name):
	"""
	Loads values from a Lexicon's config file.
	"""
	config = {}
	with open(os.path.join("lexicon", name, "lexicon.cfg"), "r", encoding="utf8") as f:
		line = f.readline()
		while line:
			# Skim lines until a value definition begins
			conf_match = re.match(">>>([^>]+)>>>\s+", line)
			if not conf_match:
				line = f.readline()
				continue
			# Accumulate the conf value until the value ends
			conf = conf_match.group(1)
			conf_value = ""
			line = f.readline()
			conf_match = re.match("<<<{0}<<<\s+".format(conf), line)
			while line and not conf_match:
				conf_value += line
				line = f.readline()
				conf_match = re.match("<<<{0}<<<\s+".format(conf), line)
			if not line:
				# TODO Not this
				raise SystemExit("Reached EOF while reading config value {}".format(conf))
			config[conf] = conf_value.strip()
	# Check that all necessary values were configured
	for config_value in ['LEXICON_TITLE', 'PROMPT', 'SESSION_PAGE', "INDEX_LIST"]:
		if config_value not in config:
			# TODO Not this either
			raise SystemExit("Error: {} not set in lexipython.cfg".format(config_value))
	return config
