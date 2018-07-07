import sys		# For argv and stderr
import os		# For reading directories
import re		# For parsing lex content
import io		# For writing pages out as UTF-8
import networkx # For pagerank analytics
from collections import defaultdict # For rank inversion in statistics

from src import utils
from src.article import LexiconArticle

def build_contents_page(articles, config):
	"""
	Builds the full HTML of the contents page.
	"""
	content = ""
	# Head the contents page with counts of written and phantom articles
	phantom_count = len([article for article in articles if article.player is None])
	if phantom_count == 0:
		content = "<p>There are <b>{0}</b> entries in this lexicon.</p>\n".format(len(articles))
	else:
		content = "<p>There are <b>{0}</b> entries, <b>{1}</b> written and <b>{2}</b> phantom.</p>\n".format(
			len(articles), len(articles) - phantom_count, phantom_count)
	# Prepare article links
	link_by_title = {article.title : "<a href=\"../article/{1}.html\"{2}>{0}</a>".format(
			article.title, article.title_filesafe,
			" class=\"phantom\"" if article.player is None else "")
			for article in articles}
	# Write the articles in alphabetical order
	content += utils.load_resource("contents.html")
	content += "<div id=\"index-order\" style=\"display:block\">\n<ul>\n"
	indices = config["INDEX_LIST"].split("\n")
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
	latest_turn = max([article.turn for article in articles if article.player is not None])
	turn_order = sorted(
		articles,
		key=lambda a: (a.turn, utils.titlesort(a.title)))
	check_off = list(turn_order)
	for turn_num in range(1, latest_turn + 1):
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
	cite_map = {
		article.title : [
			cite_tuple[1]
			for cite_tuple in article.citations.values()]
		for article in articles}
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
	# Top number of citations made
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
	# player pageranks
	content += "<div class=\"moveable\">\n"
	content += "<p><u>Player total page rank:</u><br>\n"
	players = sorted(set([article.player for article in articles if article.player is not None]))
	articles_by = {player : [a for a in articles if a.player == player] for player in players}
	player_rank = {player : sum(map(lambda a: ranks[a.title], articles)) for player, articles in articles_by.items()}
	content += "<br>\n".join(map(
		lambda kv: "{0} &ndash; {1}".format(kv[0], round(kv[1], 3)),
		sorted(player_rank.items(), key=lambda t:t[1], reverse=True)))
	content += "</p>\n"
	content += "</div>\n"
	# Player citations made
	content += "<div class=\"moveable\">\n"
	content += "<p><u>Citations made by player</u><br>\n"
	player_cite_count = {
		player : sum(map(lambda a:len(a.wcites | a.pcites), articles))
		for player, articles in articles_by.items()}
	content += "<br>\n".join(map(
		lambda kv: "{0} &ndash; {1}".format(kv[0], kv[1]),
		sorted(player_cite_count.items(), key=lambda t:t[1], reverse=True)))
	content += "</p>\n"
	content += "</div>\n"
	# player cited count
	content += "<div class=\"moveable\">\n"
	content += "<p><u>Citations made to player</u><br>\n"
	cited_times = {player : 0 for player in players}
	for article in articles:
		if article.player is not None:
			cited_times[article.player] += len(article.citedby)
	content += "<br>\n".join(map(
		lambda kv: "{0} &ndash; {1}".format(kv[0], kv[1]),
		sorted(cited_times.items(), key=lambda t:t[1], reverse=True)))
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

def build_compiled_page(articles, config):
	"""
	Builds a page compiling all articles in the Lexicon.
	"""
	pass

def build_all(path_prefix, lexicon_name):
	"""
	Builds all browsable articles and pages in the Lexicon.
	"""
	lex_path = os.path.join(path_prefix, lexicon_name)
	# Load the Lexicon's peripherals
	config = utils.load_config(lexicon_name)
	entry_skeleton = utils.load_resource("entry-page.html")
	css = utils.load_resource("lexicon.css")
	# Parse the written articles
	articles = LexiconArticle.parse_from_directory(os.path.join(lex_path, "src"))
	# At this point, the articles haven't been cross-populated,
	# so we can derive the written titles from this list
	#written_titles = [article.title for article in articles]
	# Once they've been populated, the articles list has the titles of all articles
	# Sort this by turn before title so prev/next links run in turn order
	articles = sorted(
		LexiconArticle.populate(articles),
		key=lambda a: (a.turn, utils.titlesort(a.title)))
	#phantom_titles = [article.title for article in articles if article.title not in written_titles]
	def pathto(*els):
		return os.path.join(lex_path, *els)

	# Write the redirect page
	print("Writing redirect page...")
	with open(pathto("index.html"), "w", encoding="utf8") as f:
		f.write(utils.load_resource("redirect.html").format(lexicon=config["LEXICON_TITLE"]))

	# Write the article pages
	print("Deleting old article pages...")
	for filename in os.listdir(pathto("article")):
		if filename[-5:] == ".html":
			os.remove(pathto("article", filename))
	print("Writing article pages...")
	l = len(articles)
	for idx in range(l):
		article = articles[idx]
		with open(pathto("article", article.title_filesafe + ".html"), "w", encoding="utf8") as f:
			content = article.build_default_content()
			citeblock = article.build_default_citeblock(
				None if idx == 0 else articles[idx - 1],
				None if idx == l-1 else articles[idx + 1])
			article_html = entry_skeleton.format(
				title = article.title,
				lexicon = config["LEXICON_TITLE"],
				css = css,
				logo = config["LOGO_FILENAME"],
				prompt = config["PROMPT"],
				content = content,
				citeblock = citeblock)
			f.write(article_html)
		print("    Wrote " + article.title)

	# Write default pages
	print("Writing default pages...")
	with open(pathto("contents", "index.html"), "w", encoding="utf8") as f:
		f.write(build_contents_page(articles, config))
	print("    Wrote Contents")
	with open(pathto("rules", "index.html"), "w", encoding="utf8") as f:
		f.write(build_rules_page(config))
	print("    Wrote Rules")
	with open(pathto("formatting", "index.html"), "w", encoding="utf8") as f:
		f.write(build_formatting_page(config))
	print("    Wrote Formatting")
	with open(pathto("session", "index.html"), "w", encoding="utf8") as f:
		f.write(build_session_page(config))
	print("    Wrote Session")
	with open(pathto("statistics", "index.html"), "w", encoding="utf8") as f:
		f.write(build_statistics_page(articles, config))
	print("    Wrote Statistics")