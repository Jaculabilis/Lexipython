###############################
## Lexipython Lexicon engine ##
###############################

import sys		# For argv and stderr
import os		# For reading directories
import re		# For parsing lex content
import io		# For writing pages out as UTF-8
import networkx # For pagerank analytics
from collections import defaultdict # For rank inversion in statistics

# Main article class

class LexiconArticle:
	"""
	A Lexicon article and its metadata.
	
	Members:
	author			string: the author of the article
	turn			integer: the turn the article was written for
	title			string: the article title
	title_filesafe	string: the title, escaped, used for filenames
	content			string: the HTML content, with citations replaced by format hooks
	citations		dict from format hook string to tuple of link alias and link target title
	wcites			list: titles of written articles cited
	pcites			list: titles of phantom articles cited
	citedby			list: titles of articles that cite this
	The last three are filled in by populate().
	"""
	
	def __init__(self, author, turn, title, content, citations):
		"""
		Creates a LexiconArticle object with the given parameters.
		"""
		self.author = author
		self.turn = turn
		self.title = title
		self.title_filesafe = titleescape(title)
		self.content = content
		self.citations = citations
		self.wcites = set()
		self.pcites = set()
		self.citedby = set()

	@staticmethod
	def from_file_raw(raw_content):
		"""
		Parses the contents of a Lexipython source file into a LexiconArticle
		object. If the source file is malformed, returns None.
		"""
		headers = raw_content.split('\n', 3)
		if len(headers) != 4:
			print("Header read error")
			return None
		author_header, turn_header, title_header, content_raw = headers
		# Validate and sanitize the author header
		if not author_header.startswith("# Author:"):
			print("Author header missing")
			return None
		author = author_header[9:].strip()
		# Validate and sanitize the turn header
		if not turn_header.startswith("# Turn:"):
			print("Turn header missing")
			return None
		turn = None
		try:
			turn = int(turn_header[7:].strip())
		except:
			print("Turn header error")
			return None
		# Validate and sanitize the title header
		if not title_header.startswith("# Title:"):
			print("Title header missing")
			return None
		title = titlecase(title_header[8:])
		# Parse the content and extract citations
		paras = re.split("\n\n+", content_raw.strip())
		content = ""
		citations = {}
		format_id = 1
		if not paras:
			print("No content")
		for para in paras:
			# Escape angle brackets
			para = re.sub("<", "&lt;", para)
			para = re.sub(">", "&gt;", para)
			# Replace bold and italic marks with tags
			para = re.sub(r"//([^/]+)//", r"<i>\1</i>", para)
			para = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", para)
			# Replace \\LF with <br>LF
			para = re.sub(r"\\\\\n", "<br>\n", para)
			# Abstract citations into the citation record
			link_match = re.search(r"\[\[(([^|\[\]]+)\|)?([^|\[\]]+)\]\]", para)
			while link_match:
				# Identify the citation text and cited article
				cite_text = link_match.group(2) if link_match.group(2) else link_match.group(3)
				cite_title = titlecase(link_match.group(3))
				# Record the citation
				citations["c"+str(format_id)] = (cite_text, cite_title)
				# Stitch the format id in place of the citation
				para = para[:link_match.start(0)] + "{c"+str(format_id)+"}" + para[link_match.end(0):]
				format_id += 1 # Increment to the next format citation
				link_match = re.search(r"\[\[(([^|\[\]]+)\|)?([^|\[\]]+)\]\]", para)
			# Convert signature to right-aligned
			if para[:1] == '~':
				para = "<hr><span class=\"signature\"><p>" + para[1:] + "</p></span>\n"
			else:
				para = "<p>" + para + "</p>\n"
			content += para
		return LexiconArticle(author, turn, title, content, citations)

	def build_page_content(self):
		"""
		Formats citations into the article content as normal HTML links
		and returns the result.
		"""
		format_map = {
			format_id: "<a href=\"{1}.html\"{2}>{0}</a>".format(
			cite_tuple[0], titleescape(cite_tuple[1]),
			"" if cite_tuple[1] in self.wcites else " class=\"phantom\"")
			for format_id, cite_tuple in self.citations.items()
		}
		return self.content.format(**format_map)

	def build_page_citeblock(self, prev_target, next_target):
		"""
		Builds the citeblock content HTML for use in regular article pages.
		For each defined target, links the target page as Previous or Next.
		"""
		citeblock = "<div class=\"content citeblock\">\n"
		# Prev/next links
		if next_target is not None:
			citeblock += "<p style=\"float:right\"><a href=\"{}.html\">Next &#8594;</a></p>\n".format(titleescape(next_target))
		if prev_target is not None:
			citeblock += "<p><a href=\"{}.html\">&#8592; Previous</a></p>\n".format(titleescape(prev_target))
		elif next_target is not None:
			citeblock += "<p>&nbsp;</p>\n"
		# Citations
		cites_links = [
			"<a href=\"{1}.html\"{2}>{0}</a>".format(
			title, titleescape(title),
			"" if title in self.wcites else " class=\"phantom\"")
			for title in sorted(self.wcites | self.pcites)]
		cites_str = " | ".join(cites_links)
		if len(cites_str) < 1: cites_str = "--"
		citeblock += "<p>Citations: {}</p>\n".format(cites_str)
		# Citedby
		citedby_links = [
			"<a href=\"{1}.html\">{0}</a>".format(
			title, titleescape(title))
			for title in self.citedby]
		citedby_str = " | ".join(citedby_links)
		if len(citedby_str) < 1: citedby_str = "--"
		citeblock += "<p>Cited by: {}</p>\n</div>\n".format(citedby_str)
		return citeblock

# Parsing functions for source intake

def parse_from_directory(directory):
	"""
	Reads and parses each source file in the given directory.
	Input:  directory, the path to the folder to read
	Output: a list of parsed articles
	"""
	articles = []
	print("Reading source files from", directory)
	for filename in os.listdir(directory):
		path = directory + filename
		# Read only .txt files
		if filename[-4:] == ".txt":
			print("    Parsing", filename)
			with open(path, "r", encoding="utf8") as src_file:
				raw = src_file.read()
				article = LexiconArticle.from_file_raw(raw)
				if article is None:
					print("        ERROR")
				else:
					print("        success:", article.title)
					articles.append(article)
	return articles

def populate(lexicon_articles):
	"""
	Given a list of lexicon articles, fills out citation information
	for each article and creates phantom pages for missing articles.
	"""
	article_by_title = {article.title : article for article in lexicon_articles}
	# Determine all articles that exist or should exist
	extant_titles = set([citation[1] for article in lexicon_articles for citation in article.citations])
	# Interlink all citations
	for article in lexicon_articles:
		for cite_tuple in article.citations.values():
			target = cite_tuple[1]
			# Create article objects for phantom citations
			if target not in article_by_title:
				article_by_title[target] = LexiconArticle(None, sys.maxsize, target, "<p><i>This entry hasn't been written yet.</i></p>", {})
			# Interlink citations
			if article_by_title[target].author is None:
				article.pcites.add(target)
			else:
				article.wcites.add(target)
			article_by_title[target].citedby.add(article.title)
	return list(article_by_title.values())

# Build functions

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
	content += load_resource("contents.html")
	content += "<div id=\"index-order\" style=\"display:block\">\n<ul>\n"
	indices = config["INDEX_LIST"].split("\n")
	alphabetical_order = sorted(articles, key=lambda a: a.title)
	check_off = list(alphabetical_order)
	for index_str in indices:
		content += "<h3>{0}</h3>\n".format(index_str)
		for article in alphabetical_order:
			if (titlestrip(article.title)[0].upper() in index_str):
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
	turn_order = sorted(articles, key=lambda a: (a.turn, a.title))
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
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
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
	content = load_resource("rules.html")
	# Fill in the entry skeleton
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
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
	content = load_resource("formatting.html")
	# Fill in the entry skeleton
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
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
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
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
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
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

def command_build(argv):
	if len(argv) >= 3 and (argv[2] != "partial" and argv[2] != "full"):
		print("unknown build type: " + argv[2])
		return
	# Load content
	config = load_config()
	entry_skeleton = load_resource("entry-page.html")
	css = load_resource("lexicon.css")
	articles = [article for article in parse_from_directory("raw/") if article is not None]
	written_titles = [article.title for article in articles]
	articles = sorted(populate(articles), key=lambda a: (a.turn, a.title))
	#print(articles[13].title_filesafe)
	#return
	phantom_titles = [article.title for article in articles if article.title not in written_titles]
	
	# Write the redirect page
	print("Writing redirect page...")
	with open("out/index.html", "w", encoding="utf8") as f:
		f.write(load_resource("redirect.html").format(lexicon=config["LEXICON_TITLE"]))
	
	# Write the article pages
	print("Deleting old article pages...")
	for filename in os.listdir("out/article/"):
		if filename[-5:] == ".html":
			os.remove("out/article/" + filename)
	print("Writing article pages...")
	l = len(articles)
	for idx in range(l):
		article = articles[idx]
		with open("out/article/" + article.title_filesafe + ".html", "w", encoding="utf8") as f:
			content = article.build_page_content()
			citeblock = article.build_page_citeblock(
				None if idx == 0 else articles[idx - 1].title,
				None if idx == l-1 else articles[idx + 1].title)
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
	with open("out/contents/index.html", "w", encoding="utf8") as f:
		f.write(build_contents_page(articles, config))
	print("    Wrote Contents")
	with open("out/rules/index.html", "w", encoding="utf8") as f:
		f.write(build_rules_page(config))
	print("    Wrote Rules")
	with open("out/formatting/index.html", "w", encoding="utf8") as f:
		f.write(build_formatting_page(config))
	print("    Wrote Formatting")
	with open("out/session/index.html", "w", encoding="utf8") as f:
		f.write(build_session_page(config))
	print("    Wrote Session")
	with open("out/statistics/index.html", "w", encoding="utf8") as f:
		f.write(build_statistics_page(articles, config))
	print("    Wrote Statistics")

	# Write auxiliary files
	# TODO: write graphviz file
	# TODO: write compiled lexicon page

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
