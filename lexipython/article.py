import os
import sys
import re
import utils

class LexiconCitation:
	"""
	Represents information about a single citation in a Lexicon article.

	Members:
	id          int: citation id within the article, corresponding to a "{cN}"
	            format hook
	text        string: alias text linked to the citation target
	target      string: title of the article being cited
	article     LexiconArticle: article cited, None until interlink
	"""
	def __init__(self, id, citation_text, citation_target, article=None):
		self.id = id
		self.text = citation_text
		self.target = citation_target
		self.article = article

	def __repr__(self):
		return "<LexiconCitation(id={0.id}, text=\"{0.text}\", target=\"{0.target}\")>".format(self)

	def __str__(self):
		return "<[{0.id}]:[[{0.text}|{0.target}]]>".format(self)

	def format(self, format_str):
		return format_str.format(**self.__dict__)

class LexiconArticle:
	"""
	A Lexicon article and its metadata.
	
	Members defined by __init__:
	player          string: player who wrote the article
	turn            integer: turn the article was written for
	title           string: article title
	title_filesafe  string: title, escaped, used for filenames
	content         string: HTML content, with citations replaced by format hooks
	citations       list of LexiconCitations: citations made by the article
	link_class      string: CSS class to interpolate (for styling phantoms)

	Members undefined until interlink:
	addendums       list of LexiconArticles: addendum articles to this article
	citedby         set of LexiconArticles: articles that cite this article
	prev_article    LexiconArticle: the previous article in read order
	next_article    LexiconArticle: the next article in read order
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
		self.link_class = "class=\"phantom\"" if player is None else ""
		self.addendums = []
		self.citedby = set()
		self.prev_article = None
		self.next_article = None

	def __repr__(self):
		return "<LexiconArticle(title={0.title}, turn={0.turn}, player={0.player})>".format(self)

	def __str__(self):
		return "<\"{0.title}\", {0.player} turn {0.turn}>".format(self)

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
		citations = []
		format_id = 1
		if not paras:
			print("No content")
		for para in paras:
			# Escape angle brackets
			para = re.sub("<", "&lt;", para)
			para = re.sub(">", "&gt;", para)
			# Escape curly braces
			para = re.sub("{", "&#123;", para)
			para = re.sub("}", "&#125;", para)
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
				cite_title = utils.titlecase(re.sub(r"\s+", " ", link_match.group(3)))
				# Record the citation
				cite = LexiconCitation(format_id, cite_text, cite_title)
				citations.append(cite)
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
	def interlink(lexicon_articles):
		"""
		Fills out fields on articles that require other articles for context.
		Creates phantom articles.
		"""
		# Sort out which articles are addendums and which titles are phantoms
		written_titles = set()
		cited_titles = set()
		article_by_title = {}
		written_articles_ordered = sorted(lexicon_articles, key=lambda a: (a.turn, a.title))
		for written_article in written_articles_ordered:
			# Track main articles by title
			if written_article.title not in written_titles:
				article_by_title[written_article.title] = written_article
				written_titles.add(written_article.title)
			# Append addendums to their parents
			else:
				parent = article_by_title[written_article.title]
				parent.addendums.append(written_article)
			# Collect all cited titles
			for citation in written_article.citations:
				cited_titles.add(citation.target)
		# Create articles for each phantom title
		for title in cited_titles - written_titles:
			phantom_article = LexiconArticle(
				None, sys.maxsize, title,
				"<p><i>This entry hasn't been written yet.</i></p>", {})
			article_by_title[title] = phantom_article
		# To interlink the articles, each citation needs to have its .article
		# filled in, and that article needs its citedby updated.
		for parent in article_by_title.values():
			under_title = [parent] + parent.addendums
			for citing_article in under_title:
				for citation in citing_article.citations:
					target_article = article_by_title[citation.target]
					citation.article = target_article
					target_article.citedby.add(citing_article)
		# Sort the articles by turn and title, then fill in prev/next fields
		articles_ordered = sorted(article_by_title.values(), key=lambda a: (a.turn, utils.titlesort(a.title)))
		for i in range(len(articles_ordered)):
			articles_ordered[i].prev_article = articles_ordered[i-1] if i != 0 else None
			articles_ordered[i].next_article = articles_ordered[i+1] if i != len(articles_ordered)-1 else None
		return articles_ordered

	def build_default_content(self):
		"""
		Builds the contents of the content div for an article page.
		"""
		content = ""
		# Build the main article content block
		main_body = self.build_default_article_body()
		content += "<div class=\"contentblock\"><h1>{}</h1>{}</div>\n".format(
			self.title, main_body)
		# Build the main citation content block
		main_citations = self.build_default_citeblock()
		if main_citations:
			content += "<div class=\"contentblock citeblock\">{}</div>\n".format(
				main_citations)
		# Build any addendum content blocks
		for addendum in self.addendums:
			add_body = addendum.build_default_article_body()
			content += "<div class=\"contentblock\">{}</div>\n".format(add_body)
			add_citations = addendum.build_default_citeblock()
			if add_citations:
				content += "<div class=\"contentblock\">{}</div>\n".format(
					add_citations)
		# Build the prev/next block
		prev_next = self.build_prev_next_block(
			self.prev_article, self.next_article)
		if prev_next:
			content += "<div class=\"contentblock citeblock\">{}</div>\n".format(
				prev_next)
		return content

	def build_default_article_body(self):
		"""
		Formats citations into the article text and returns the article body.
		"""
		format_map = {
			"c"+str(c.id) : c.format("<a {article.link_class} "\
				"href=\"{article.title_filesafe}.html\">{text}</a>")
			for c in self.citations
		}
		return self.content.format(**format_map)

	def build_default_citeblock(self):
		"""
		Builds the contents of a citation contentblock. Skips sections with no
		content.
		"""
		content = ""
		# Citations
		cites_titles = set()
		cites_links = []
		for citation in sorted(self.citations, key=lambda c: (utils.titlesort(c.target), c.id)):
			if citation.target not in cites_titles:
				cites_titles.add(citation.target)
				cites_links.append(
					citation.format(
						"<a {article.link_class} href=\"{article.title_filesafe}.html\">{article.title}</a>"))
		cites_str = " / ".join(cites_links)
		if len(cites_str) > 0:
			content += "<p>Citations: {}</p>\n".format(cites_str)
		# Citedby
		citedby_titles = set()
		citedby_links = []
		for article in sorted(self.citedby, key=lambda a: (utils.titlesort(a.title), a.turn)):
			if article.title not in citedby_titles:
				citedby_titles.add(article.title)
				citedby_links.append(
					"<a {0.link_class} href=\"{0.title_filesafe}.html\">{0.title}</a>".format(article))
		citedby_str = " / ".join(citedby_links)
		if len(citedby_str) > 0:
			content += "<p>Cited by: {}</p>\n".format(citedby_str)

		return content

	def build_prev_next_block(self, prev_article, next_article):
		"""
		For each defined target, links the target page as Previous or Next.
		"""
		content = ""
		# Prev/next links:
		if next_article is not None or prev_article is not None:
			prev_link = ("<a {0.link_class} href=\"{0.title_filesafe}.html\">&#8592; Previous</a>".format(
				prev_article)
				if prev_article is not None else "")
			next_link = ("<a {0.link_class} href=\"{0.title_filesafe}.html\">Next &#8594;</a>".format(
				next_article)
				if next_article is not None else "")
			content += "<table><tr>\n<td>{}</td>\n<td>{}</td>\n</table></tr>\n".format(
				prev_link, next_link)
		return content
