###############################
## Lexipython Lexicon engine ##
###############################

import sys		# For argv and stderr
import os		# For reading directories
import re		# For parsing lex content
import io		# For writing pages out as UTF-8
import networkx # For pagerank analytics
from collections import defaultdict # For rank inversion in statistics

# Utility functions for handling titles and filenames

def titlecase(s):
	s = s.strip()
	return s[:1].capitalize() + s[1:]

def as_filename(s):
	"""Makes a string filename-safe."""
	# Strip out <, >, :, ", ', /, \, |, ?, and *
	s = re.sub(r"[<>:\"'/\\|?*]", '', s)
	# Strip out Unicode for -
	s = re.sub(r"[^\x00-\x7F]+", '-', s)
	# Strip out whitespace for _
	s = re.sub(r"\s+", '_', s)
	return s

def titlestrip(s):
	"""Strips certain prefixes for title sorting."""
	if s.startswith("The "): return s[4:]
	if s.startswith("An "): return s[3:]
	if s.startswith("A "): return s[2:]
	return s

def link_formatter(written_articles):
	"""
	Creates a lambda that formats citation links and handles the phantom class.
	Input:  written_articles, a list of article titles to format as live links
	Output: a lambda (fid, alias, title) -> link_string
	"""
	return lambda fid, alias, title: "<a href=\"{1}.html\"{2}>{0}</a>".format(
			alias, as_filename(title),
			"" if title in written_articles else " class=\"phantom\""
		)

# Parsing functions for source intake

def parse_lex_header(header_para):
	"""
	Parses the header paragraph of a lex file.
	Input:  header_para, raw header paragraph from the lex file
	Output: {"error": <error message>} if there was an error, otherwise
	        {"title": <article title>, "filename": <article filename>}
	"""
	# The title, which is also translated to the filename, heads the article after the #
	title_match = re.match("#(.+)", header_para)
	if not title_match:
		return {"error": "No match for title"}
	title = titlecase(title_match.group(1).strip())
	if not title:
		return {"error": "Could not parse header as title"}
	return {"title": title, "filename": as_filename(title)}

def parse_lex_content(paras):
	"""
	Parses the content paragraphs of a lex file.
	Input:  paras, a list of raw paragraphs from the lex file
	Output: {"error": <error message>} if there was an error, otherwise
	        {"content": <article HTML content>,
			 "citations": {<format id>: (link text, link target)}}
	"""
	parsed = {"content": "", "citations": {}}
	format_id = 1 # Each citation will be ID'd by {c#} for formatting later
	for para in paras:
		# Escape angle brackets
		para = re.sub("<", "&lt;", para)
		para = re.sub(">", "&gt;", para)
		# Replace bold and italic marks with tags
		para = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", para)
		para = re.sub(r"\/\/([^\/]+)\/\/", r"<i>\1</i>", para)
		# Replace \\LF with <br>LF
		para = re.sub(r"\\\\\n", "<br>\n", para)
		# Abstract citations into the citation record
		link_match = re.search(r"\[\[(([^|\[\]]+)\|)?([^|\[\]]+)\]\]", para)
		while link_match:
			# Identify the citation text and cited article
			cite_text = link_match.group(2) if link_match.group(2) else link_match.group(3)
			cite_title = titlecase(link_match.group(3).strip())
			# Record the citation
			parsed["citations"]["c"+str(format_id)] = (cite_text, cite_title)
			# Stitch the format id in place of the citation
			para = para[:link_match.start(0)] + "{c"+str(format_id)+"}" + para[link_match.end(0):]
			format_id += 1 # Increment to the next format citation
			link_match = re.search(r"\[\[(([^|\[\]]+)\|)?([^|\[\]]+)\]\]", para)
		# Convert signature to right-aligned
		if para[:1] == '~':
			para = "<hr><span class=\"signature\"><p>" + para[1:] + "</p></span>\n"
		else:
			para = "<p>" + para + "</p>\n"
		parsed["content"] += para
	if not parsed["content"]:
		return {"error": "No content parsed"}
	return parsed

def parse_lex(lex_contents):
	"""
	Parses the contents of a lex file into HTML and abstracts citations.
	Input:  lex_contents, the read contents of a lex file
	Output: A dictionary in the following format:
	{"title": <article title>, "filename": <article filename>,
	 "content": <article HTML content>, 
	 "citations": {<format id>: (link text, link target)}}
	"""
	parsed_article = {}
	# Split the file into paragraphs
	paras = re.split("\n\n+", lex_contents)
	# Parse the title from the header
	title_parsed = parse_lex_header(paras.pop(0))
	if "error" in title_parsed:
		return title_parsed
	parsed_article.update(title_parsed)
	# Parse each paragraph
	content_parsed = parse_lex_content(paras)
	if "error" in content_parsed:
		return content_parsed
	parsed_article.update(content_parsed)
	# Return the fully abstracted article
	return parsed_article

def parse_lex_from_directory(directory):
	"""
	Reads and parses each lex file in the given directory.
	Input:  directory, the path to the folder to read
	Output: a list of parsed lex file structures
	"""
	lexes = []
	print("Reading lex files from", directory)
	for filename in os.listdir(directory):
		path = directory + filename
		# Read only .lex files
		if path[-4:] == ".lex":
			print("    Parsing", path)
			with open(path, "r", encoding="utf8") as lex_file:
				lex_raw = lex_file.read()
				parsed_lex = parse_lex(lex_raw)
				if "error" in parsed_lex:
					print("        ERROR:", parsed_lex["error"])
				else:
					print("        success:", parsed_lex["title"])
					lexes.append(parsed_lex)
	return lexes

def load_resource(filename, cache={}):
	if filename not in cache:
		cache[filename] = open("resources/" + filename, "r", encoding="utf8").read()
	return cache[filename]

def load_config():
	config = {}
	with open("lexicon.cfg", "r", encoding="utf8") as f:
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
				raise SystemExit("Reached EOF while reading config value {}".format(conf))
			config[conf] = conf_value.strip()
	# Check that all necessary values were configured
	for config_value in ['LEXICON_TITLE', 'SIDEBAR_CONTENT', 'SESSION_PAGE', "INDEX_LIST"]:
		if config_value not in config:
			raise SystemExit("Error: {} not set in lexipython.cfg".format(config_value))
	return config

# Building functions for output

def make_cite_map(lex_list):
	"""
	Compiles all citation information into a single map.
	Input:  lex_list, a list of lex structures
	Output: a map from article titles to cited titles
	"""
	cite_map = {}
	for lex in lex_list:
		cited_titles = [cite_tuple[1] for format_id, cite_tuple in lex["citations"].items()]
		cite_map[lex["title"]] = sorted(set(cited_titles), key=titlestrip)
	return cite_map

def format_content(lex, format_func):
	"""
	Formats citations into the lex content according to the provided function.
	Input:  lex, a lex structure
	        formatted_key, the key to store the formatted content under
	        format_func, a function matching (fid, alias, dest) -> citation HTML
	Output: lex content formatted according to format_func
	"""
	format_map = {
		format_id: format_func(format_id, cite_tuple[0], cite_tuple[1])
		for format_id, cite_tuple in lex["citations"].items()
	}
	return lex["content"].format(**format_map)

def citation_lists(title, cite_map):
	"""
	Returns the citation lists for an article.
	Input:  title, an article title
			cite_map, generated by make_cite_map
	Output: a list of cited article titles
	        a list of titles of article citing this article
	"""
	citers = [citer_title
		for citer_title, cited_titles in cite_map.items()
		if title in cited_titles]
	return cite_map[title] if title in cite_map else [], citers

def build_article_page(lex, cite_map, config):
	"""
	Builds the full HTML of an article page.
	Input:  lex, a lex structure
			cite_map, generated by make_cite_map
			config, a dict of config values
	Output: the full HTML as a string
	"""
	lf = link_formatter(cite_map.keys())
	# Build the article content
	content = format_content(lex, lf)
	# Build the article citeblock
	cites, citedby = citation_lists(lex["title"], cite_map)
	cites_str = " | ".join([lf(None, title, title) for title in cites])
	if len(cites_str) < 1: cites_str = "--"
	citedby_str = " | ".join([lf(None, title, title) for title in citedby])
	if len(citedby_str) < 1: citedby_str = "--"
	citeblock = ""\
		"<div class=\"content citeblock\">\n"\
		"<p>Citations: {cites}</p>\n"\
		"<p>Cited by: {citedby}</p>\n"\
		"</div>\n".format(
			cites=cites_str,
			citedby=citedby_str)
	# Fill in the entry skeleton
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
	return entry_skeleton.format(
		title=lex["title"],
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		sidebar=config["SIDEBAR_HTML"],
		content=content,
		citeblock=citeblock)

def build_phantom_page(title, cite_map, config):
	"""
	Builds the full HTML of a phantom page.
	Input:  title, the phantom title
			cite_map, generated by make_cite_map
			config, a dict of config values
	Output: the full HTML as a string
	"""
	lf = link_formatter(cite_map.keys())
	# Fill in the content with filler
	content = "<p><i>This entry hasn't been written yet.</i></p>"
	# Build the stub citeblock
	cites, citedby = citation_lists(title, cite_map)
	citedby_str = " | ".join([lf(None, title, title) for title in citedby])
	citeblock = ""\
		"<div class=\"content citeblock\">\n"\
		"<p>Cited by: {citedby}</p>\n"\
		"</div>\n".format(
			citedby=citedby_str)
	# Fill in the entry skeleton
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
	return entry_skeleton.format(
		title=title,
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		sidebar=config["SIDEBAR_HTML"],
		content=content,
		citeblock=citeblock)

def build_stub_page(title, cite_map, config):
	"""
	Builds the full HTML of a stub page.
	Input:  title, the stub title
			cite_map, generated by make_cite_map
			config, a dict of config values
	Output: the full HTML as a string
	"""
	lf = link_formatter(cite_map.keys())
	# Fill in the content with filler
	content = "<p>[The handwriting is completely illegible.]</p>\n"\
		"<hr><span class=\"signature\"><p>Ersatz Scrivener</p></span>\n"
	# Build the stub citeblock
	citedby = [citer_title
		for citer_title, cited_titles in cite_map.items()
		if title in cited_titles]
	citedby_str = " | ".join([lf(None, title, title) for title in citedby])
	citeblock = ""\
		"<div class=\"content citeblock\">\n"\
		"<p>Citations: [Illegible]</p>\n"\
		"<p>Cited by: {citedby}</p>\n"\
		"</div>\n".format(
			citedby=citedby_str)
	# Fill in the entry skeleton
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
	return entry_skeleton.format(
		title=title,
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		sidebar=config["SIDEBAR_HTML"],
		content=content,
		citeblock=citeblock)

def build_index_page(cite_map, config):
	"""
	Builds the full HTML of the index page.
	Input:	cite_map, generated by make_cite_map
			config, a dict of config values
	Output:	the HTML of the index page
	"""
	# Count up all the titles
	titles = set(cite_map.keys()) | set([title for cited_titles in cite_map.values() for title in cited_titles])
	titles = sorted(set(titles), key=titlestrip)
	content = ""
	if len(titles) == len(cite_map.keys()):
		content = "<p>There are <b>{0}</b> entries in this lexicon.</p>\n<ul>\n".format(len(titles))
	else:
		content = "<p>There are <b>{0}</b> entries, <b>{1}</b> written and <b>{2}</b> phantom.</p>\n<ul>\n".format(
			len(titles), len(cite_map.keys()), len(titles) - len(cite_map.keys()))
	# Write all of the entries out as links under their indices
	lf = link_formatter(cite_map.keys())
	indices = config["INDEX_LIST"].split("\n")
	for index_str in indices:
		content += "<h3>{0}</h3>".format(index_str)
		index_titles = []
		for c in index_str.upper():
			for title in titles:
				if (titlestrip(title)[0] == c):
					index_titles.append(title)
		for title in index_titles:
			titles.remove(title)
			content += "<li>"
			content += lf(None, title, title)
			content += "</li>\n"
	if len(titles) > 0:
		content += "<h3>&c.</h3>".format(index_str)
		for title in titles:
			content += "<li>"
			content += lf(None, title, title)
			content += "</li>\n"
	content += "</ul>\n"
	# Fill in the entry skeleton
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
	return entry_skeleton.format(
		title="Index of " + config["LEXICON_TITLE"],
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		sidebar=config["SIDEBAR_HTML"],
		content=content,
		citeblock="")

def build_rules_page(config):
	"""
	Builds the full HTML of the rules page.
	Input:	config, a dict of config values
	Output:	the HTML of the rules page
	"""
	content = load_resource("rules.html")
	# Fill in the entry skeleton
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
	return entry_skeleton.format(
		title="Rules",
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		sidebar=config["SIDEBAR_HTML"],
		content=content,
		citeblock="")

def build_formatting_page(config):
	"""
	Builds the full HTML of the formatting page.
	Input:	config, a dict of config values
	Output:	the HTML of the formatting page
	"""
	content = load_resource("formatting.html")
	# Fill in the entry skeleton
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
	return entry_skeleton.format(
		title="Formatting",
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		sidebar=config["SIDEBAR_HTML"],
		content=content,
		citeblock="")

def build_session_page(config):
	"""
	Builds the full HTML of the session page.
	Input:	config, a dict of config values
	Output:	the HTML of the session page
	"""
	session_lex = parse_lex(config["SESSION_PAGE"])
	content = format_content(session_lex, lambda fid,alias,dest: "<u>" + alias + "</u>")
	# Fill in the entry skeleton
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
	return entry_skeleton.format(
		title=session_lex["title"],
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		sidebar=config["SIDEBAR_HTML"],
		content=content,
		citeblock="")

def build_statistics_page(cite_map, config):
	"""
	Builds the full HTML of the statistics page.
	Input:	citation_map, a dictionary returned by make_cite_map
			config, a dict of config values
	Output:	the HTML of the statistics page
	"""
	content = ""
	# Compute the pagerank
	content += "<p><u>Top 10 by page rank:</u><br>\n"
	G = networkx.Graph()
	for citer, citeds in cite_map.items():
		for cited in citeds:
			G.add_edge(citer, cited)
	ranks = networkx.pagerank(G)
	sranks = sorted(ranks.items(), key=lambda x: x[1], reverse=True)
	ranking = list(enumerate(map(lambda x: x[0], sranks)))
	content += "<br>\n".join(map(lambda x: "{0} - {1}".format(x[0]+1, x[1]), ranking[:10]))
	content += "</p>\n"
	# Count the top number of citations made from
	content += "<p><u>Most citations made from:</u><br>\n"
	citation_tally = [(kv[0], len(kv[1])) for kv in cite_map.items()]
	citation_count = defaultdict(list)
	for title, count in citation_tally: citation_count[count].append(title)
	content += "<br>\n".join(map(
			lambda kv: "{0} - {1}".format(kv[0], "; ".join(kv[1])),
			sorted(citation_count.items(), reverse=True)[:3]))
	content += "</p>\n"
	# Count the top number of citations made to
	content += "<p><u>Most citations made to:</u><br>\n"
	all_cited = set([title for cites in cite_map.values() for title in cites])
	cited_by_map = { cited: [citer for citer in cite_map.keys() if cited in cite_map[citer]] for cited in all_cited }
	cited_tally = [(kv[0], len(kv[1])) for kv in cited_by_map.items()]
	cited_count = defaultdict(list)
	for title, count in cited_tally: cited_count[count].append(title)
	content += "<br>\n".join(map(
			lambda kv: "{0} - {1}".format(kv[0], "; ".join(kv[1])),
			sorted(cited_count.items(), reverse=True)[:3]))
	#cited_count = map(lambda kv: (kv[0], len(kv[1])), cited_by_map.items())
	#cited_count_sort = sorted(cited_count, key=lambda x: x[1], reverse=True)
	#top_cited_count = [kv for kv in cited_count_sort if kv[1] >= cited_count_sort[:5][-1][1]]
	#content += "<br>\n".join(map(lambda x: "{0} - {1}".format(x[1], x[0]), top_cited_count))
	content += "</p>\n"
	# Fill in the entry skeleton
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
	return entry_skeleton.format(
		title="Statistics",
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		sidebar=config["SIDEBAR_HTML"],
		content=content,
		citeblock="")

# Summative functions

def command_build(argv):
	if len(argv) >= 3 and (argv[2] != "partial" and argv[2] != "full"):
		print("unknown build type: " + argv[2])
		return
	# Set up the entries
	config = load_config()
	sidebar_parsed = parse_lex(config["SIDEBAR_CONTENT"])
	config["SIDEBAR_HTML"] = format_content(sidebar_parsed, lambda fid,alias,dest: alias)
	lexes = parse_lex_from_directory("raw/")
	cite_map = make_cite_map(lexes)
	written_entries = cite_map.keys()
	phantom_entries = set([title for cites in cite_map.values() for title in cites if title not in written_entries])
	# Clear the folder
	print("Clearing old HTML files")
	for filename in os.listdir("out/"):
		if filename[-5:] == ".html":
			os.remove("out/" + filename)
	# Write the written entries
	print("Writing written articles...")
	for lex in lexes:
		page = build_article_page(lex, cite_map, config)
		with open("out/" + lex["filename"] + ".html", "w", encoding="utf8") as f:
			f.write(page)
		print("    Wrote " + lex["title"])
	# Write the unwritten entries
	if len(phantom_entries) > 0:
		if len(argv) < 3 or argv[2] == "partial":
			print("Writing phantom articles...")
			for title in phantom_entries:
				page = build_phantom_page(title, cite_map, config)
				with open("out/" + as_filename(title) + ".html", "w", encoding="utf8") as f:
					f.write(page)
				print("    Wrote " + title)
		elif argv[2] == "full":
			print("Writing stub articles...")
			for title in phantom_entries:
				page = build_stub_page(title, cite_map, config)
				with open("out/" + as_filename(title) + ".html", "w", encoding="utf8") as f:
					f.write(page)
				print("    Wrote " + title)
		else:
			print("ERROR: build type was " + argv[2])
			return
	# Write the default pages
	print("Writing default pages")
	page = build_rules_page(config)
	with open("out/rules.html", "w", encoding="utf8") as f:
		f.write(page)
	print("    Wrote Rules")
	page = build_formatting_page(config)
	with open("out/formatting.html", "w", encoding="utf8") as f:
		f.write(page)
	print("    Wrote Formatting")
	page = build_index_page(cite_map, config)
	with open("out/index.html", "w", encoding="utf8") as f:
		f.write(page)
	print("    Wrote Index")
	page = build_session_page(config)
	with open("out/session.html", "w", encoding="utf8") as f:
		f.write(page)
	print("    Wrote Session")
	page = build_statistics_page(cite_map, config)
	with open("out/stats.html", "w", encoding="utf8") as f:
		f.write(page)
	print("    Wrote Statistics")

def main():
	if len(sys.argv) < 2:
		print("Available commands:")
		print(" - build [partial] : Build the lexicon and generate phantom stubs for all unwritten articles.")
		print(" - build full      : Build the lexicon and generate Ersatz pages for all unwritten articles.")
	elif sys.argv[1] == "build":
		command_build(sys.argv)
	else:
		print("Unknown command: " + sys.argv[1])

if __name__ == "__main__":
	main()
