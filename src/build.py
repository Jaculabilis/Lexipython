import sys		# For argv and stderr
import os		# For reading directories
import re		# For parsing lex content
import io		# For writing pages out as UTF-8
import networkx # For pagerank analytics
from collections import defaultdict # For rank inversion in statistics

import src.utils as utils

def build_contents_page(articles, config):
	"""
	Builds the full HTML of the contents page.
	"""
	content = ""
	# Article counts
	phantom_count = len([article for article in articles if article.author is None])
	if phantom_count == 0:
		content = "<p>There are <b>{0}</b> entries in this lexicon.</p>\n".format(len(articles))
	else:
		content = "<p>There are <b>{0}</b> entries, <b>{1}</b> written and <b>{2}</b> phantom.</p>\n".format(
			len(articles), len(articles) - phantom_count, phantom_count)
	# Prepare article links
	link_by_title = {article.title : "<a href=\"../article/{1}.html\"{2}>{0}</a>".format(
			article.title, article.title_filesafe,
			"" if article.author is not None else " class=\"phantom\"")
			for article in articles}
	# Write the articles in alphabetical order
	content += utils.load_resource("contents.html")
	content += "<div id=\"index-order\" style=\"display:block\">\n<ul>\n"
	indices = config["INDEX_LIST"].split("\n")
	alphabetical_order = sorted(articles, key=lambda a: utils.titlecase(a.title))
	check_off = list(alphabetical_order)
	for index_str in indices:
		content += "<h3>{0}</h3>\n".format(index_str)
		for article in alphabetical_order:
			if (utils.titlestrip(article.title)[0].upper() in index_str):
				check_off.remove(article)
				content += "<li>"
				content += link_by_title[article.title]
				content += "</li>\n"
	if len(check_off) > 0:
		content += "<h3>&c.</h3>\n".format(index_str)
		for article in check_off:
			content += "<li>"
			content += link_by_title[article.title]
			content += "</li>\n"
	content += "</ul>\n</div>\n"
	# Write the articles in turn order
	content += "<div id=\"turn-order\" style=\"display:none\">\n<ul>\n"
	latest_turn = max([article.turn for article in articles if article.author is not None])
	turn_order = sorted(articles, key=lambda a: (a.turn, utils.titlecase(a.title)))
	check_off = list(turn_order)
	for turn_num in range(1, latest_turn + 1):
		content += "<h3>Turn {0}</h3>\n".format(turn_num)
		for article in turn_order:
			if article.turn == turn_num:
				check_off.remove(article)
				content += "<li>"
				content += link_by_title[article.title]
				content += "</li>\n"
	if len(check_off) > 0:
		content += "<h3>Unwritten</h3>\n"
		for article in check_off:
			content += "<li>"
			content += link_by_title[article.title]
			content += "</li>\n"
	content += "</ul>\n</div>\n"
	# Fill in the page skeleton
	entry_skeleton = utils.load_resource("entry-page.html")
	css = utils.load_resource("lexicon.css")
	return entry_skeleton.format(
		title="Index of " + config["LEXICON_TITLE"],
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		prompt=config["PROMPT"],
		content=content,
		citeblock="")

def build_rules_page(config):
	"""
	Builds the full HTML of the rules page.
	"""
	content = utils.load_resource("rules.html")
	# Fill in the entry skeleton
	entry_skeleton = utils.load_resource("entry-page.html")
	css = utils.load_resource("lexicon.css")
	return entry_skeleton.format(
		title="Rules",
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		prompt=config["PROMPT"],
		content=content,
		citeblock="")

def build_formatting_page(config):
	"""
	Builds the full HTML of the formatting page.
	"""
	content = utils.load_resource("formatting.html")
	# Fill in the entry skeleton
	entry_skeleton = utils.load_resource("entry-page.html")
	css = utils.load_resource("lexicon.css")
	return entry_skeleton.format(
		title="Formatting",
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		prompt=config["PROMPT"],
		content=content,
		citeblock="")

def build_session_page(config):
	"""
	Builds the full HTML of the session page.
	"""
	# Fill in the entry skeleton
	entry_skeleton = utils.load_resource("entry-page.html")
	css = utils.load_resource("lexicon.css")
	return entry_skeleton.format(
		title=config["LEXICON_TITLE"],
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		prompt=config["PROMPT"],
		content=config["SESSION_PAGE"],
		citeblock="")

def build_statistics_page(articles, config):
	"""
	Builds the full HTML of the statistics page.
	"""
	content = ""
	cite_map = {article.title : [cite_tuple[1] for cite_tuple in article.citations.values()] for article in articles}
	# Pages by pagerank
	content += "<div class=\"moveable\">\n"
	content += "<p><u>Top 10 pages by page rank:</u><br>\n"
	G = networkx.Graph()
	for citer, citeds in cite_map.items():
		for cited in citeds:
			G.add_edge(citer, cited)
	ranks = networkx.pagerank(G)
	sranks = sorted(ranks.items(), key=lambda x: x[1], reverse=True)
	ranking = list(enumerate(map(lambda x: x[0], sranks)))
	content += "<br>\n".join(map(lambda x: "{0} &ndash; {1}".format(x[0]+1, x[1]), ranking[:10]))
	content += "</p>\n"
	content += "</div>\n"
	# Top numebr of citations made
	content += "<div class=\"moveable\">\n"
	content += "<p><u>Most citations made from:</u><br>\n"
	citation_tally = [(kv[0], len(kv[1])) for kv in cite_map.items()]
	citation_count = defaultdict(list)
	for title, count in citation_tally: citation_count[count].append(title)
	content += "<br>\n".join(map(
			lambda kv: "{0} &ndash; {1}".format(kv[0], "; ".join(kv[1])),
			sorted(citation_count.items(), reverse=True)[:3]))
	content += "</p>\n"
	content += "</div>\n"
	# Top number of times cited
	content += "<div class=\"moveable\">\n"
	content += "<p><u>Most citations made to:</u><br>\n"
	all_cited = set([title for cites in cite_map.values() for title in cites])
	cited_by_map = { cited: [citer for citer in cite_map.keys() if cited in cite_map[citer]] for cited in all_cited }
	cited_tally = [(kv[0], len(kv[1])) for kv in cited_by_map.items()]
	cited_count = defaultdict(list)
	for title, count in cited_tally: cited_count[count].append(title)
	content += "<br>\n".join(map(
			lambda kv: "{0} &ndash; {1}".format(kv[0], "; ".join(kv[1])),
			sorted(cited_count.items(), reverse=True)[:3]))
	content += "</p>\n"
	content += "</div>\n"
	# Author pageranks
	content += "<div class=\"moveable\">\n"
	content += "<p><u>Author total page rank:</u><br>\n"
	authors = sorted(set([article.author for article in articles if article.author is not None]))
	articles_by = {author : [a for a in articles if a.author == author] for author in authors}
	author_rank = {author : sum(map(lambda a: ranks[a.title], articles)) for author, articles in articles_by.items()}
	content += "<br>\n".join(map(
		lambda kv: "{0} &ndash; {1}".format(kv[0], round(kv[1], 3)),
		sorted(author_rank.items(), key=lambda t:-t[1])))
	content += "</p>\n"
	content += "</div>\n"
	# Author citations made
	content += "<div class=\"moveable\">\n"
	content += "<p><u>Citations made by author</u><br>\n"
	author_cite_count = {author : sum(map(lambda a:len(a.wcites | a.pcites), articles)) for author, articles in articles_by.items()}
	content += "<br>\n".join(map(
		lambda kv: "{0} &ndash; {1}".format(kv[0], kv[1]),
		sorted(author_cite_count.items(), key=lambda t:-t[1])))
	content += "</p>\n"
	content += "</div>\n"
	# Author cited count
	content += "<div class=\"moveable\">\n"
	content += "<p><u>Citations made to author</u><br>\n"
	cited_times = {author : 0 for author in authors}
	for article in articles:
		if article.author is not None:
			cited_times[article.author] += len(article.citedby)
	content += "<br>\n".join(map(
		lambda kv: "{0} &ndash; {1}".format(kv[0], kv[1]),
		sorted(cited_times.items(), key=lambda t:-t[1])))
	content += "</p>\n"
	content += "</div>\n"
	
	# Fill in the entry skeleton
	entry_skeleton = utils.load_resource("entry-page.html")
	css = utils.load_resource("lexicon.css")
	return entry_skeleton.format(
		title="Statistics",
		lexicon=config["LEXICON_TITLE"],
		css=css,
		logo=config["LOGO_FILENAME"],
		prompt=config["PROMPT"],
		content=content,
		citeblock="")

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

# Summative functions


	# Write auxiliary files
	# TODO: write graphviz file
	# TODO: write compiled lexicon page
