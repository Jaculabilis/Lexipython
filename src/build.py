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
	"""
	content = ""

	# Top pages by pagerank
	# Compute pagerank for each article
	G = networkx.Graph()
	for article in articles:
		for citation in article.citations:
			G.add_edge(article.title, citation.target)
	rank_by_article = networkx.pagerank(G)
	# Get the top ten articles by pagerank
	top_pageranks = reverse_statistics_dict(rank_by_article)[:10]
	# Replace the pageranks with ordinals
	top_ranked = enumerate(map(lambda x: x[1], top_pageranks), start=1)
	# Format the ranks into strings
	top_ranked_items = itemize(top_ranked)
	# Write the statistics to the page
	content += "<div class=\"contentblock\">\n"
	content += "<u>Top 10 articles by page rank:</u><br>\n"
	content += "<br>\n".join(top_ranked_items)
	content += "</div>\n"

	# Top number of citations made
	citations_made = {article.title : len(article.citations) for article in articles}
	top_citations = reverse_statistics_dict(citations_made)[:3]
	top_citations_items = itemize(top_citations)
	content += "<div class=\"contentblock\">\n"
	content += "<u>Top articles by citations made:</u><br>\n"
	content += "<br>\n".join(top_citations_items)
	content += "</div>\n"

	# Top number of times cited
	citations_to = {article.title : len(article.citedby) for article in articles}
	top_cited = reverse_statistics_dict(citations_to)[:3]
	top_cited_items = itemize(top_cited)
	content += "<div class=\"contentblock\">\n"
	content += "<u>Most cited articles:</u><br>\n"
	content += "<br>\n".join(top_cited_items)
	content += "</div>\n"

	# Top article length, roughly by words
	article_length = {}
	for article in articles:
		format_map = {
			"c"+str(c.id): c.text
			for c in article.citations
		}
		plain_content = article.content.format(**format_map)
		article_length[article.title] = len(plain_content.split())
	top_length = reverse_statistics_dict(article_length)[:3]
	top_length_items = itemize(top_length)
	content += "<div class=\"contentblock\">\n"
	content += "<u>Longest articles:</u><br>\n"
	content += "<br>\n".join(top_length_items)
	content += "</div>\n"

	# Total word count
	content += "<div class=\"contentblock\">\n"
	content += "<u>Total word count:</u><br>\n"
	content += str(sum(article_length.values()))
	content += "</div>\n"

	# Player pageranks
	# Add addendums and recompute pagerank
	for article in articles:
		for addendum in article.addendums:
			for citation in addendum.citations:
				addendum_title = "{0.title}-T{0.turn}".format(addendum)
				G.add_edge(addendum_title, citation.target)
	rank_by_article = networkx.pagerank(G)
	players = sorted(set([article.player for article in articles if article.player is not None]))
	pagerank_by_player = {player: 0 for player in players}
	for article in articles:
		if article.player is not None:
			pagerank_by_player[article.player] += (rank_by_article[article.title]
				if article.title in rank_by_article else 0)
			for addendum in article.addendums:
				addendum_title = "{0.title}-T{0.turn}".format(addendum)
				pagerank_by_player[addendum_title] += (rank_by_article[addendum_title]
					if addendum_title in rank_by_article else 0)
	for player in players:
		pagerank_by_player[player] = round(pagerank_by_player[player], 3)
	player_rank = reverse_statistics_dict(pagerank_by_player)
	player_rank_items = itemize(player_rank)
	content += "<div class=\"contentblock\">\n"
	content += "<u>Player total page rank:</u><br>\n"
	content += "<br>\n".join(player_rank_items)
	content += "</div>\n"

	# Player citations made
	cite_count_by_player = {player: 0 for player in players}
	for article in articles:
		if article.player is not None:
			unique_citations = set([a.target for a in article.citations])
			cite_count_by_player[article.player] += len(unique_citations)
			for addendum in article.addendums:
				cite_count_by_player[addendum.player] += len(addendum.citations)
	player_cites_made_ranks = reverse_statistics_dict(cite_count_by_player)
	player_cites_made_items = itemize(player_cites_made_ranks)
	content += "<div class=\"contentblock\">\n"
	content += "<u>Citations made by player:</u><br>\n"
	content += "<br>\n".join(player_cites_made_items)
	content += "</div>\n"

	# Player cited count
	cited_times = {player : 0 for player in players}
	for article in articles:
		if article.player is not None:
			cited_times[article.player] += len(article.citedby)
	cited_times_ranked = reverse_statistics_dict(cited_times)
	cited_times_items = itemize(cited_times_ranked)
	content += "<div class=\"contentblock\">\n"
	content += "<u>Citations made to player:</u><br>\n"
	content += "<br>\n".join(cited_times_items)
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
	# Sort by turn and title
	turn_order = sorted(
		articles,
		key=lambda a: (a.turn, utils.titlesort(a.title)))

	# Build the content of each article
	css = utils.load_resource("lexicon.css")
	css += "\n"\
		"body { background: #ffffff; }\n"\
		"sup { vertical-align: top; font-size: 0.6em; }\n"
	content = "<html>\n"\
		"<head>\n"\
		"<title>{lexicon}</title>\n"\
		"<style>\n"\
		"{css}\n"\
		"</style>\n"\
		"<body>\n"\
		"<h1>{lexicon}</h1>".format(
			lexicon=config["LEXICON_TITLE"],
			css=css)
	for article in turn_order:
		# Stitch in superscripts for citations
		format_map = {
			format_id: "{}<sup>{}</sup>".format(cite_tuple[0], format_id[1:])
			for format_id, cite_tuple in article.citations.items()
		}
		article_body = article.content.format(**format_map)
		# Stitch a page-break-avoid div around the header and first paragraph
		article_body = article_body.replace("</p>", "</p></div>", 1)
		# Append the citation block
		cite_list = "<br>\n".join(
			"{}. {}\n".format(format_id[1:], cite_tuple[1])
			for format_id, cite_tuple in sorted(
				article.citations.items(),
				key=lambda t:int(t[0][1:])))
		cite_block = "" if article.player is None else ""\
			"<p><i>Citations:</i><br>\n"\
			"{}\n</p>".format(cite_list)
		article_block = "<div style=\"page-break-inside:avoid;\">\n"\
			"<h2>{}</h2>\n"\
			"{}\n"\
			"{}\n".format(article.title, article_body, cite_block)
		content += article_block

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
			#contentblock = article.build_default_contentblock()
			#citeblock = article.build_default_citeblock(
			#	None if idx == 0 else articles[idx - 1],
			#	None if idx == l-1 else articles[idx + 1])
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

	# Check that authors aren't citing themselves
	print("Running citation checks...")
	article_by_title = {article.title : article for article in articles}
	#for article in articles:
	#	for _, tup in article.citations.items():
	#		cited = article_by_title[tup[1]]
	#		if article.player == cited.player:
	#			print("    {2}: {0} cites {1}".format(article.title, cited.title, cited.player))

	print()
