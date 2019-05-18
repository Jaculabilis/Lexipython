# Standard library imports
import os		# For reading directories
import re		# For parsing lex content

# Application imports
import utils
from article import LexiconArticle
from statistics import LexiconStatistics


class LexiconPage:
	"""
	An abstraction layer around formatting a Lexicon page skeleton with kwargs
	so that kwargs that are constant across pages aren't repeated.
	"""

	def __init__(self, skeleton=None, page=None):
		self.kwargs = {}
		self.skeleton = skeleton
		if page is not None:
			self.skeleton = page.skeleton
			self.kwargs = dict(page.kwargs)

	def add_kwargs(self, **kwargs):
		self.kwargs.update(kwargs)

	def format(self, **kwargs):
		total_kwargs = {**self.kwargs, **kwargs}
		return self.skeleton.format(**total_kwargs)

def article_matches_index(index_type, pattern, article):
	if index_type == "char":
		return utils.titlesort(article.title)[0].upper() in pattern.upper()
	if index_type == "prefix":
		return article.title.startswith(pattern)
	if index_type == "etc":
		return True
	raise ValueError("Unknown index type: '{}'".format(index_type))

def build_contents_page(config, page, articles):
	"""
	Builds the full HTML of the contents page.
	"""
	content = "<div class=\"contentblock\">"

	# Head the contents page with counts of written and phantom articles
	phantom_count = len([article for article in articles if article.player is None])
	if phantom_count == 0:
		content += "<p>There are <b>{0}</b> entries in this lexicon.</p>\n".format(len(articles))
	else:
		content += "<p>There are <b>{0}</b> entries, <b>{1}</b> written and <b>{2}</b> phantom.</p>\n".format(
			len(articles), len(articles) - phantom_count, phantom_count)

	# Prepare article links
	link_by_title = {article.title : "<a href=\"../article/{1}.html\"{2}>{0}</a>".format(
			article.title, article.title_filesafe,
			" class=\"phantom\"" if article.player is None else "")
			for article in articles}

	# Determine index order
	indices = config['INDEX_LIST'].split("\n")
	index_by_pri = {}
	index_list_order = []
	for index in indices:
		match = re.match(r"([^[:]+)(\[([-\d]+)\])?:(.+)", index)
		index_type = match.group(1)
		pattern = match.group(4)
		try:
			pri_s = match.group(3)
			pri = int(pri_s) if pri_s else 0
		except:
			raise TypeError("Could not parse index pri '{}' in '{}'".format(pri_s, index))
		if pri not in index_by_pri:
			index_by_pri[pri] = []
		index_by_pri[pri].append((index_type, pattern))
		index_list_order.append(pattern)

	# Assign articles to indices
	articles_by_index = {pattern: [] for pattern in index_list_order}
	titlesort_order = sorted(
		articles,
		key=lambda a: utils.titlesort(a.title))
	for article in titlesort_order:
		# Find the first index that matches
		matched = False
		for pri, indices in sorted(index_by_pri.items(), reverse=True):
			for index_type, pattern in indices:
				# Try to match the index
				if article_matches_index(index_type, pattern, article):
					articles_by_index[pattern].append(article)
					matched = True
				# Break out once a match is found
				if matched:
					break
			if matched:
				break
		if not matched:
			raise KeyError("No index matched article '{}'".format(article.title))

	# Write index order div
	content += utils.load_resource("contents.html")
	content += "<div id=\"index-order\" style=\"display:{}\">\n<ul>\n".format(
		"block" if config["DEFAULT_SORT"] == "index" else "none")
	for pattern in index_list_order:
		# Write the index header
		content += "<h3>{0}</h3>\n".format(pattern)
		# Write all matches articles
		for article in articles_by_index[pattern]:
			content += "<li>{}</li>\n".format(link_by_title[article.title])
	content += "</ul>\n</div>\n"

	# Write turn order div
	content += "<div id=\"turn-order\" style=\"display:{}\">\n<ul>\n".format(
		"block" if config["DEFAULT_SORT"] == "turn" else "none")
	turn_numbers = [article.turn for article in articles if article.player is not None]
	first_turn, last_turn = min(turn_numbers), max(turn_numbers)
	turn_order = sorted(
		articles,
		key=lambda a: (a.turn, utils.titlesort(a.title)))
	check_off = list(turn_order)
	for turn_num in range(first_turn, last_turn + 1):
		content += "<h3>Turn {0}</h3>\n".format(turn_num)
		for article in turn_order:
			if article.turn == turn_num:
				check_off.remove(article)
				content += "<li>{}</li>\n".format(link_by_title[article.title])
	if len(check_off) > 0:
		content += "<h3>Unwritten</h3>\n"
		for article in check_off:
			content += "<li>{}</li>\n".format(link_by_title[article.title])
	content += "</ul>\n</div>\n"

	# Write by-player div
	content += "<div id=\"player-order\" style=\"display:{}\">\n<ul>\n".format(
		"block" if config["DEFAULT_SORT"] == "player" else "none")
	articles_by_player = {}
	extant_phantoms = False
	for article in turn_order:
		if article.player is not None:
			if article.player not in articles_by_player:
				articles_by_player[article.player] = []
			articles_by_player[article.player].append(article)
		else:
			extant_phantoms = True
	for player, player_articles in sorted(articles_by_player.items()):
		content += "<h3>{0}</h3>\n".format(player)
		for article in player_articles:
			content += "<li>{}</li>\n".format(link_by_title[article.title])
	if extant_phantoms:
		content += "<h3>Unwritten</h3>\n"
		for article in titlesort_order:
			if article.player is None:
				content += "<li>{}</li>\n".format(link_by_title[article.title])
	content += "</ul>\n</div>\n"

	content += "</div>\n"
	# Fill in the page skeleton
	return page.format(title="Index", content=content)

def build_rules_page(page):
	"""
	Builds the full HTML of the rules page.
	"""
	content = utils.load_resource("rules.html")
	# Fill in the entry skeleton
	return page.format(title="Rules", content=content)

def build_formatting_page(page):
	"""
	Builds the full HTML of the formatting page.
	"""
	content = utils.load_resource("formatting.html")
	# Fill in the entry skeleton
	return page.format(title="Formatting", content=content)

def build_session_page(page, session_content):
	"""
	Builds the full HTML of the session page.
	"""
	# Fill in the entry skeleton
	content = "<div class=\"contentblock\">{}</div>".format(session_content)
	return page.format(title="Session", content=content)

def build_statistics_page(config, page, articles):
	# Read the config file for which stats to publish.
	lines = config['STATISTICS'].split("\n")
	stats = []
	for line in lines:
		stat, toggle = line.split()
		if toggle == "on":
			stats.append("stat_" + stat)

	# Create all the stats blocks.
	lexicon_stats = LexiconStatistics(articles)
	stats_blocks = []
	for stat in stats:
		if hasattr(lexicon_stats, stat):
			stats_blocks.append(getattr(lexicon_stats, stat)())
		else:
			print("ERROR: Bad stat {}".format(stat))
	content = "\n".join(stats_blocks)

	# Fill in the entry skeleton
	return page.format(title="Statistics", content=content)

def build_graphviz_file(cite_map):
	"""
	Builds a citation graph in dot format for Graphviz.
	"""
	result = []
	result.append("digraph G {\n")
	# Node labeling
	written_entries = list(cite_map.keys())
	phantom_entries = set([title for cites in cite_map.values() for title in cites if title not in written_entries])
	node_labels = [title[:20] for title in written_entries + list(phantom_entries)]
	node_names = [hash(i) for i in node_labels]
	for i in range(len(node_labels)):
		result.append("{} [label=\"{}\"];\n".format(node_names[i], node_labels[i]))
	# Edges
	for citer in written_entries:
		for cited in cite_map[citer]:
			result.append("{}->{};\n".format(hash(citer[:20]), hash(cited[:20])))
	# Return result
	result.append("overlap=false;\n}\n")
	return "".join(result)#"…"

def build_compiled_page(articles, config):
	"""
	Builds a page compiling all articles in the Lexicon.
	"""
	articles = sorted(
		articles,
		key=lambda a: (utils.titlesort(a.title)))

	# Write the header
	content = "<html><head><title>{}</title>"\
		"<style>span.signature {{ text-align: right; }} "\
		"sup {{ vertical-align: top; font-size: 0.6em; }} "\
		"u {{ text-decoration-color: #888888; }}</style>"\
		"</head><body>\n".format(config["LEXICON_TITLE"])

	# Write each article
	for article in articles:
		# Article title
		content += "<div style=\"page-break-inside:avoid;\"><h2>{0.title}</h2>".format(article)

		# Article content
		format_map = {
			"c"+str(c.id) : c.format("<u>{text}</u><sup>{id}</sup>")
			for c in article.citations
		}
		article_content = article.content.format(**format_map)
		article_content = article_content.replace("</p>", "</p></div>", 1)
		content += article_content

		# Article citations
		cite_list = "<br>".join(
			c.format("{id}. {target}")
			for c in article.citations)
		cite_block = "<p>{}</p>".format(cite_list)
		content += cite_block

		# Addendums
		for addendum in article.addendums:
			# Addendum content
			format_map = {
				"c"+str(c.id) : c.format("<u>{text}</u><sup>{id}</sup>")
				for c in addendum.citations
			}
			article_content = addendum.content.format(**format_map)
			content += article_content

			# Addendum citations
			cite_list = "<br>".join(
				c.format("{id}. {target}")
				for c in addendum.citations)
			cite_block = "<p>{}</p>".format(cite_list)
			content += cite_block

	content += "</body></html>"
	return content

def latex_from_markdown(raw_content):
	content = ""
	headers = raw_content.split('\n', 3)
	player_header, turn_header, title_header, content_raw = headers
	if not turn_header.startswith("# Turn:"):
		print("Turn header missing or corrupted")
		return None
	turn = int(turn_header[7:].strip())
	if not title_header.startswith("# Title:"):
		print("Title header missing or corrupted")
		return None
	title = utils.titlecase(title_header[8:])
	#content += "\\label{{{}}}\n".format(title)
	#content += "\\section*{{{}}}\n\n".format(title)
	# Parse content
	paras = re.split("\n\n+", content_raw.strip())
	for para in paras:
		# Escape things
		para = re.sub("&mdash;", "---", para)
		para = re.sub("&", "\\&", para)
		para = re.sub(r"\"(?=\w)", "``", para)
		para = re.sub(r"(?<=\w)\"", "''", para)
		# Replace bold and italic marks with commands
		para = re.sub(r"//([^/]+)//", r"\\textit{\1}", para)
		para = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", para)
		# Footnotify citations
		link_match = re.search(r"\[\[(([^|\[\]]+)\|)?([^|\[\]]+)\]\]", para)
		while link_match:
			# Identify the citation text and cited article
			cite_text = link_match.group(2) if link_match.group(2) else link_match.group(3)
			cite_title = utils.titlecase(re.sub(r"\s+", " ", link_match.group(3)))
			# Stitch the title into a footnote
			para = (para[:link_match.start(0)] + cite_text + "\\footnote{" + 
				cite_title + 
				", p. \\pageref{" + str(hash(cite_title)) + "}" + 
				"}" + para[link_match.end(0):])
			link_match = re.search(r"\[\[(([^|\[\]]+)\|)?([^|\[\]]+)\]\]", para)
		# Convert signature to right-aligned
		if para[:1] == '~':
			para = "\\begin{flushright}\n" + para[1:] + "\n\\end{flushright}\n\n"
		else:
			para = para + "\n\n"
		content += para
	return title, turn, content

def latex_from_directory(directory):
	articles = {}
	for filename in os.listdir(directory):
		path = os.path.join(directory, filename)
		# Read only .txt files
		if filename[-4:] == ".txt":
			with open(path, "r", encoding="utf8") as src_file:
				raw = src_file.read()
				title, turn, latex = latex_from_markdown(raw)
				if title not in articles:
					articles[title] = {}
				articles[title][turn] = latex

	# Write the preamble
	content = "\\documentclass[12pt,a4paper,twocolumn,twoside]{article}\n"\
		"\\usepackage[perpage]{footmisc}\n"\
		"\\begin{document}\n"\
		"\n"

	for title in sorted(articles.keys(), key=lambda t: utils.titlesort(t)):
		under_title = articles[title]
		turns = sorted(under_title.keys())
		latex = under_title[turns[0]]

		# Section header
		content += "\\label{{{}}}\n".format(hash(title))
		content += "\\section*{{{}}}\n\n".format(title)

		# Section content
		#format_map = {
		#	"c"+str(c.id) : c.format("\\footnote{{{target}}}")
		#	for c in article.citations
		#}
		#article_content = article.content.format(**format_map)
		content += latex

		# Addendums
		for turn in turns[1:]:
			#content += "\\vspace{6pt}\n\\hrule\n\\vspace{6pt}\n\n"
			content += "\\begin{center}\n$\\ast$~$\\ast$~$\\ast$\n\\end{center}\n\n"

			latex = under_title[turn]
			#format_map = {
			#	"c"+str(c.id) : c.format("\\footnote{{{target}}}")
			#	for c in addendum.citations
			#}
			#article_content = addendum.content.format(**format_map)
			content += latex

	content += "\\end{document}"

	content = re.sub(r"\"(?=\w)", "``", content)
	content = re.sub(r"(?<=\w)\"", "''", content)

	return content

def parse_sort_type(sort):
	if sort in "?byindex":
		return "?byindex"
	if sort in "?byturn":
		return "?byturn"
	if sort in "?byplayer":
		return "?byplayer"
	return ""

def build_all(path_prefix, lexicon_name):
	"""
	Builds all browsable articles and pages in the Lexicon.
	"""
	lex_path = os.path.join(path_prefix, lexicon_name)
	# Load the Lexicon's peripherals
	config = utils.load_config(lexicon_name)
	page_skeleton = utils.load_resource("page-skeleton.html")
	page = LexiconPage(skeleton=page_skeleton)
	page.add_kwargs(
		lexicon=config["LEXICON_TITLE"],
		logo=config["LOGO_FILENAME"],
		prompt=config["PROMPT"],
		sort=parse_sort_type(config["DEFAULT_SORT"]))
	# Parse the written articles
	articles = LexiconArticle.parse_from_directory(os.path.join(lex_path, "src"))
	# Once they've been populated, the articles list has the titles of all articles
	# Sort this by turn before title so prev/next links run in turn order
	articles = sorted(
		LexiconArticle.interlink(articles),
		key=lambda a: (a.turn, utils.titlesort(a.title)))

	def pathto(*els):
		return os.path.join(lex_path, *els)

	# Write the redirect page
	print("Writing redirect page...")
	with open(pathto("index.html"), "w", encoding="utf8") as f:
		f.write(utils.load_resource("redirect.html").format(
			lexicon=config["LEXICON_TITLE"], sort=config["DEFAULT_SORT"]))

	# Write the article pages
	print("Deleting old article pages...")
	for filename in os.listdir(pathto("article")):
		if filename[-5:] == ".html":
			os.remove(pathto("article", filename))
	print("Writing article pages...")
	l = len(articles)
	for idx in range(l):
		article = articles[idx]
		with open(pathto("article", article.title_filesafe + ".html"), "w", encoding="utf-8") as f:
			content = article.build_default_content()
			article_html = page.format(
				title = article.title,
				content = content)
			f.write(article_html)
		print("    Wrote " + article.title)

	# Write default pages
	print("Writing default pages...")
	with open(pathto("contents", "index.html"), "w", encoding="utf-8") as f:
		f.write(build_contents_page(config, page, articles))
	print("    Wrote Contents")
	with open(pathto("rules", "index.html"), "w", encoding="utf-8") as f:
		f.write(build_rules_page(page))
	print("    Wrote Rules")
	with open(pathto("formatting", "index.html"), "w", encoding="utf-8") as f:
		f.write(build_formatting_page(page))
	print("    Wrote Formatting")
	with open(pathto("session", "index.html"), "w", encoding="utf-8") as f:
		f.write(build_session_page(page, config["SESSION_PAGE"]))
	print("    Wrote Session")
	with open(pathto("statistics", "index.html"), "w", encoding="utf-8") as f:
		f.write(build_statistics_page(config, page, articles))
	print("    Wrote Statistics")

	# Write auxiliary pages
	if "PRINTABLE_FILE" in config and config["PRINTABLE_FILE"]:
		with open(pathto(config["PRINTABLE_FILE"]), "w", encoding="utf-8") as f:
			f.write(build_compiled_page(articles, config))
		print("    Wrote compiled page to " + config["PRINTABLE_FILE"])

	with open(pathto("editor.html"), "w", encoding="utf-8") as f:
		editor = utils.load_resource("editor.html")
		writtenArticles = ""
		phantomArticles = ""
		for article in articles:
			citedby = {'"' + citer.player + '"' for citer in article.citedby}
			if article.player is None:
				phantomArticles += "{{title: \"{0}\", citedby: [{1}]}},".format(
					article.title.replace("\"", "\\\""),
					",".join(sorted(citedby)))
			else:
				writtenArticles += "{{title: \"{0}\", author: \"{1.player}\"}},".format(
					article.title.replace("\"", "\\\""), article)
		nextTurn = 0
		if articles:
			nextTurn = max([article.turn for article in articles if article.player is not None]) + 1
		editor = editor.replace("//writtenArticles", writtenArticles)
		editor = editor.replace("//phantomArticles", phantomArticles)
		editor = editor.replace("TURNNUMBER", str(nextTurn))
		f.write(editor)

	# Check that authors aren't citing themselves
	print("Running citation checks...")
	for parent in articles:
		for article in [parent] + parent.addendums:
			for citation in article.citations:
				if article.player == citation.article.player:
					print("    {2}: {0} cites {1}".format(article.title, citation.target, article.player))

	print()
