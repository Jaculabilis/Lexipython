import os
import sys
import re
import src.utils as utils

class LexiconArticle:
	"""
	A Lexicon article and its metadata.
	
	Members:
	player          string: the player of the article
	turn            integer: the turn the article was written for
	title           string: the article title
	title_filesafe  string: the title, escaped, used for filenames
	content         string: the HTML content, with citations replaced by format hooks
	citations       dict mapping format hook string to tuple of link alias and link target title
	wcites          list: titles of written articles cited
	pcites          list: titles of phantom articles cited
	citedby         list: titles of articles that cite this
	The last three are filled in by populate().
	"""

	def __init__(self, player, turn, title, content, citations):
		"""
		Creates a LexiconArticle object with the given parameters.
		"""
		self.player = player
		self.turn = turn
		self.title = title
		self.title_filesafe = utils.titleescape(title)
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
		player_header, turn_header, title_header, content_raw = headers
		# Validate and sanitize the player header
		if not player_header.startswith("# Player:"):
			print("Player header missing or corrupted")
			return None
		player = player_header[9:].strip()
		# Validate and sanitize the turn header
		if not turn_header.startswith("# Turn:"):
			print("Turn header missing or corrupted")
			return None
		turn = None
		try:
			turn = int(turn_header[7:].strip())
		except:
			print("Turn header error")
			return None
		# Validate and sanitize the title header
		if not title_header.startswith("# Title:"):
			print("Title header missing or corrupted")
			return None
		title = utils.titlecase(title_header[8:])
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
				cite_title = utils.titlecase(link_match.group(3))
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
		return LexiconArticle(player, turn, title, content, citations)

	@staticmethod
	def parse_from_directory(directory):
		"""
		Reads and parses each source file in the given directory.
		Input:  directory, the path to the folder to read
		Output: a list of parsed articles
		"""
		articles = []
		print("Reading source files from", directory)
		for filename in os.listdir(directory):
			path = os.path.join(directory, filename)
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

	@staticmethod
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
				if article_by_title[target].player is None:
					article.pcites.add(target)
				else:
					article.wcites.add(target)
				article_by_title[target].citedby.add(article.title)
		return list(article_by_title.values())

	def build_default_content(self):
		"""
		Formats citations into the article content as normal HTML links
		and returns the result.
		"""
		format_map = {
			format_id: "<a href=\"{1}.html\"{2}>{0}</a>".format(
			cite_tuple[0], utils.titleescape(cite_tuple[1]),
			"" if cite_tuple[1] in self.wcites else " class=\"phantom\"")
			for format_id, cite_tuple in self.citations.items()
		}
		return self.content.format(**format_map)

	def build_default_citeblock(self, prev_article, next_article):
		"""
		Builds the citeblock content HTML for use in regular article pages.
		For each defined target, links the target page as Previous or Next.
		"""
		citeblock = "<div class=\"content citeblock\">\n"
		# Prev/next links
		if next_article is not None:
			citeblock += "<p style=\"float:right\"><a href=\"{}.html\"{}>Next &#8594;</a></p>\n".format(
				next_article.title_filesafe, " class=\"phantom\"" if next_article.player is None else "")
		if prev_article is not None:
			citeblock += "<p><a href=\"{}.html\"{}>&#8592; Previous</a></p>\n".format(
				prev_article.title_filesafe, " class=\"phantom\"" if prev_article.player is None else "")
		if next_article is None and prev_article is None:
			citeblock += "<p>&nbsp;</p>\n"
		# Citations
		cites_links = [
			"<a href=\"{1}.html\"{2}>{0}</a>".format(
			title, utils.titleescape(title),
			"" if title in self.wcites else " class=\"phantom\"")
			for title in sorted(self.wcites | self.pcites)]
		cites_str = " | ".join(cites_links)
		if len(cites_str) < 1: cites_str = "&mdash;"
		citeblock += "<p>Citations: {}</p>\n".format(cites_str)
		# Citedby
		citedby_links = [
			"<a href=\"{1}.html\">{0}</a>".format(
			title, utils.titleescape(title))
			for title in self.citedby]
		citedby_str = " | ".join(citedby_links)
		if len(citedby_str) < 1: citedby_str = "&mdash;"
		citeblock += "<p>Cited by: {}</p>\n</div>\n".format(citedby_str)
		return citeblock
