import sys		# For argv and stderr
import os		# For reading directories
import re		# For parsing lex content
import io		# For writing pages out as UTF-8
import networkx # For pagerank analytics
from collections import defaultdict # For rank inversion in statistics

from src import utils
from src.article import LexiconArticle

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

def build_contents_page(page, articles, index_list):
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
	# Write the articles in alphabetical order
	content += utils.load_resource("contents.html")
	content += "<div id=\"index-order\" style=\"display:none\">\n<ul>\n"
	indices = index_list.split("\n")
	alphabetical_order = sorted(
		articles,
		key=lambda a: utils.titlesort(a.title))
	check_off = list(alphabetical_order)
	for index_str in indices:
		content += "<h3>{0}</h3>\n".format(index_str)
		for article in alphabetical_order:
			if (utils.titlesort(article.title)[0].upper() in index_str):
				check_off.remove(article)
				content += "<li>{}</li>\n".format(link_by_title[article.title])
	if len(check_off) > 0:
		content += "<h3>&c.</h3>\n"
		for article in check_off:
			content += "<li>{}</li>\n".format(link_by_title[article.title])
	content += "</ul>\n</div>\n"
	# Write the articles in turn order
	content += "<div id=\"turn-order\" style=\"display:none\">\n<ul>\n"
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

def reverse_statistics_dict(stats, reverse=True):
	"""
	Transforms a dictionary mapping titles to a value into a list of values
	and lists of titles. The list is sorted by the value, and the titles are
	sorted alphabetically.
	"""
	rev = {}
	for key, value in stats.items():
		if value not in rev:
			rev[value] = []
		rev[value].append(key)
	for key, value in rev.items():
		rev[key] = sorted(value, key=lambda t: utils.titlesort(t))
	return sorted(rev.items(), key=lambda x:x[0], reverse=reverse)

def itemize(stats_list):
	return map(lambda x: "{0} &ndash; {1}".format(x[0], "; ".join(x[1])), stats_list)

def build_statistics_page(page, articles):
	"""
	Builds the full HTML of the statistics page.

	The existence of addendum articles complicates how some statistics are
	computed. An addendum is an article, with its own author, body, and
	citations, but in a Lexicon it exists appended to another article. To handle
	this, we distinguish an _article_ from a _page_. An article is a unit parsed
	from a single source file. A page is a main article and all addendums under
	the same title.
	"""
	min_turn = 0
	max_turn = 0
	article_by_title = {}
	page_by_title = {}
	players = set()
	for main_article in articles:
		key = main_article.title
		page_by_title[key] = [main_article]
		page_by_title[key].extend(main_article.addendums)
		for article in [main_article] + main_article.addendums:
			# Disambiguate articles by appending turn number to the title
			key = "{0.title} (T{0.turn})".format(article)
			article_by_title[key] = article
			if article.player is not None:
				min_turn = min(min_turn, article.turn)
				max_turn = max(max_turn, article.turn)
				players.add(article.player)
	content = ""
	stat_block = "<div class=\"contentblock\"><u>{0}</u><br>{1}</div>\n"

	# Top pages by pagerank
	# Compute pagerank for each page, including all articles
	G = networkx.Graph()
	for page_title, articles in page_by_title.items():
		for article in articles:
			for citation in article.citations:
				G.add_edge(page_title, citation.target)
	pagerank_by_title = networkx.pagerank(G)
	for page_title, articles in page_by_title.items():
		if page_title not in pagerank_by_title:
			pagerank_by_title[page_title] = 0
	# Get the top ten articles by pagerank
	top_pageranks = reverse_statistics_dict(pagerank_by_title)[:10]
	# Replace the pageranks with ordinals
	top_ranked = enumerate(map(lambda x: x[1], top_pageranks), start=1)
	# Format the ranks into strings
	top_ranked_items = itemize(top_ranked)
	# Write the statistics to the page
	content += stat_block.format(
		"Top 10 articles by page rank:",
		"<br>".join(top_ranked_items))

	# Pages cited/cited by
	pages_cited    = {page_title: set() for page_title in page_by_title.keys()}
	pages_cited_by = {page_title: set() for page_title in page_by_title.keys()}
	for page_title, articles in page_by_title.items():
		for article in articles:
			for citation in article.citations:
				pages_cited[page_title].add(citation.target)
				pages_cited_by[citation.target].add(page_title)
	for page_title, cite_titles in pages_cited.items():
		pages_cited[page_title] = len(cite_titles)
	for page_title, cite_titles in pages_cited_by.items():
		pages_cited_by[page_title] = len(cite_titles)

	top_citations = reverse_statistics_dict(pages_cited)[:3]
	top_citations_items = itemize(top_citations)
	content += stat_block.format(
		"Cited the most pages:",
		"<br>".join(top_citations_items))
	top_cited = reverse_statistics_dict(pages_cited_by)[:3]
	top_cited_items = itemize(top_cited)
	content += stat_block.format(
		"Cited by the most pages:",
		"<br>".join(top_cited_items))

	# Top article length
	article_length_by_title = {}
	cumulative_article_length_by_turn = {
		turn_num: 0
		for turn_num in range(min_turn, max_turn + 1)
	}
	for article_title, article in article_by_title.items():
		format_map = {
			"c"+str(c.id): c.text
			for c in article.citations
		}
		plain_content = article.content.format(**format_map)
		word_count = len(plain_content.split())
		article_length_by_title[article_title] = word_count
		for turn_num in range(min_turn, max_turn + 1):
			if article.turn <= turn_num:
				cumulative_article_length_by_turn[turn_num] += word_count
	top_length = reverse_statistics_dict(article_length_by_title)[:3]
	top_length_items = itemize(top_length)
	content += stat_block.format(
		"Longest articles:",
		"<br>".join(top_length_items))

	# Total word count
	len_list = [(str(k), [str(v)]) for k,v in cumulative_article_length_by_turn.items()]
	content += stat_block.format(
		"Aggregate word count by turn:",
		"<br>".join(itemize(len_list)))

	# Player pageranks
	pagerank_by_player = {player: 0 for player in players}
	for page_title, articles in page_by_title.items():
		page_author = articles[0].player
		if page_author is not None:
			pagerank_by_player[page_author] += pagerank_by_title[page_title]
	for player, pagerank in pagerank_by_player.items():
		pagerank_by_player[player] = round(pagerank, 3)
	player_rank = reverse_statistics_dict(pagerank_by_player)
	player_rank_items = itemize(player_rank)
	content += stat_block.format(
		"Player aggregate page rank:",
		"<br>".join(player_rank_items))

	# Player citations made
	pages_cited_by_player = {player: 0 for player in players}
	for article_title, article in article_by_title.items():
		if article.player is not None:
			pages_cited_by_player[article.player] += len(article.citations)
	player_cites_made_ranks = reverse_statistics_dict(pages_cited_by_player)
	player_cites_made_items = itemize(player_cites_made_ranks)
	content += "<div class=\"contentblock\">\n"
	content += "<u>Citations made by player:</u><br>\n"
	content += "<br>\n".join(player_cites_made_items)
	content += "</div>\n"

	# Player cited count
	pages_cited_by_by_player = {player: 0 for player in players}
	for page_title, articles in page_by_title.items():
		page_author = articles[0].player
		if page_author is not None:
			pages_cited_by_by_player[page_author] += len(articles[0].citedby)
	cited_times_ranked = reverse_statistics_dict(pages_cited_by_by_player)
	cited_times_items = itemize(cited_times_ranked)
	content += "<div class=\"contentblock\">\n"
	content += "<u>Citations made to article by player:</u><br>\n"
	content += "<br>\n".join(cited_times_items)
	content += "</div>\n"

	# Lowest pagerank of written articles
	exclude = [a.title for a in articles if a.player is None]
	rank_by_written_only = {k:v for k,v in pagerank_by_title.items() if k not in exclude}
	pageranks = reverse_statistics_dict(rank_by_written_only)
	bot_ranked = list(enumerate(map(lambda x: x[1], pageranks), start=1))[-10:]
	# Format the ranks into strings
	bot_ranked_items = itemize(bot_ranked)
	content += "<div class=\"contentblock\">\n"
	content += "<u>Bottom 10 articles by pagerank:</u><br>\n"
	content += "<br>\n".join(bot_ranked_items)
	content += "</div>\n"

	# Undercited articles
	undercited = {
		page_title: len(articles[0].citedby)
		for page_title, articles in page_by_title.items()
		if len(articles[0].citedby) < 2}
	undercited_items = itemize(reverse_statistics_dict(undercited))
	content += "<div class=\"contentblock\">\n"
	content += "<u>Undercited articles:</u><br>\n"
	content += "<br>\n".join(undercited_items)
	content += "</div>\n"

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
		sort=config["DEFAULT_SORT"])
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
		f.write(build_contents_page(page, articles, config["INDEX_LIST"]))
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
		f.write(build_statistics_page(page, articles))
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
