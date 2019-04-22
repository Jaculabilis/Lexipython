import os
import re
import io
from urllib import parse
import pkg_resources

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
	s = s[:64]                  # Limit to 64 characters
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
		binary = pkg_resources.resource_string("resources", filename)
		unistr = binary.decode("utf-8")
		cache[filename] = unistr
	return cache[filename]

def parse_config_file(f):
	"""Parses a Lexipython config file."""
	config = {}
	line = f.readline()
	while line:
		# Skim lines until a value definition begins
		conf_match = re.match(r">>>([^>]+)>>>\s+", line)
		if not conf_match:
			line = f.readline()
			continue
		# Accumulate the conf value until the value ends
		conf = conf_match.group(1)
		conf_value = ""
		line = f.readline()
		conf_match = re.match(r"<<<{0}<<<\s+".format(conf), line)
		while line and not conf_match:
			conf_value += line
			line = f.readline()
			conf_match = re.match(r"<<<{0}<<<\s+".format(conf), line)
		if not line:
			raise EOFError("Reached EOF while reading config value {}".format(conf))
		config[conf] = conf_value.strip()
	return config

def load_config(name):
	"""
	Loads values from a Lexicon's config file.
	"""
	with open(os.path.join("lexicon", name, "lexicon.cfg"), "r", encoding="utf8") as f:
		config = parse_config_file(f)
	# Check that no values are missing that are present in the default config
	with io.StringIO(load_resource("lexicon.cfg")) as f:
		default_config = parse_config_file(f)
	missing_keys = []
	for key in default_config.keys():
		if key not in config:
			missing_keys.append(key)
	if missing_keys:
		raise KeyError("{} missing config values for: {}".format(name, " ".join(missing_keys)))
	return config
