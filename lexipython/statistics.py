# Third party imports
try:
	import networkx # For pagerank analytics
	NETWORKX_ENABLED = True
except:
	NETWORKX_ENABLED = False

# Application imports
from utils import titlesort


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
		rev[key] = sorted(value, key=lambda t: titlesort(t))
	return sorted(rev.items(), key=lambda x:x[0], reverse=reverse)


def itemize(stats_list):
	"""
	Formats a list consisting of tuples of ranks and lists of ranked items.
	"""
	return map(lambda x: "{0} &ndash; {1}".format(x[0], "; ".join(x[1])), stats_list)


class LexiconStatistics():
	"""
	A wrapper for a persistent statistics context with some precomputed
	values around for convenience.

	The existence of addendum articles complicates how some statistics are
	computed. An addendum is an article, with its own author, body, and
	citations, but in a Lexicon it exists appended to another article. To handle
	this, we distinguish an _article_ from a _page_. An article is a unit parsed
	from a single source file. A page is a main article and all addendums under
	the same title.
	"""

	def __init__(self, articles):
		self.articles = articles
		self.min_turn = 0
		self.max_turn = 0
		self.players = set()
		self.title_to_article = {}
		self.title_to_page = {}
		self.stat_block = "<div class=\"contentblock\"><u>{0}</u><br>{1}</div>\n"
		# Pagerank may not be computable if networkx isn't installed.
		self.title_to_pagerank = None

		for main_article in articles:
			page_title = main_article.title
			self.title_to_page[page_title] = [main_article]
			self.title_to_page[page_title].extend(main_article.addendums)
			for article in self.title_to_page[page_title]:
				# Disambiguate articles by appending turn number to the title
				key = "{0.title} (T{0.turn})".format(article)
				self.title_to_article[key] = article
				if article.player is not None:
					# Phantoms have turn MAXINT by convention
					self.min_turn = min(self.min_turn, article.turn)
					self.max_turn = max(self.max_turn, article.turn)
					self.players.add(article.player)

	def _try_populate_pagerank(self):
		"""Computes pagerank if networkx is imported."""
		if NETWORKX_ENABLED and self.title_to_pagerank is None:
			# Create a citation graph linking page titles.
			G = networkx.Graph()
			for page_title, articles in self.title_to_page.items():
				for article in articles:
					for citation in article.citations:
						G.add_edge(page_title, citation.target)

			# Compute pagerank on the page citation graph.
			self.title_to_pagerank = networkx.pagerank(G)
			# Any article with no links in the citation graph have no pagerank.
			# Assign these pagerank 0 to avoid key errors or missing pages in
			# the stats.
			for page_title, articles in self.title_to_page.items():
				if page_title not in self.title_to_pagerank:
					self.title_to_pagerank[page_title] = 0

	def stat_top_pagerank(self):
		"""Computes the top 10 pages by pagerank."""
		self._try_populate_pagerank()

		if not self.title_to_pagerank:
			# If networkx was not successfully imported, skip the pagerank.
			top_ranked_items = "networkx must be installed to compute pageranks."

		else:
			# Get the top ten articles by pagerank.
			top_pageranks = reverse_statistics_dict(self.title_to_pagerank)[:10]
			# Replace the pageranks with ordinals.
			top_ranked = enumerate(map(lambda x: x[1], top_pageranks), start=1)
			# Format the ranks into strings.
			top_ranked_items = itemize(top_ranked)

		# Format the statistics block.
		return self.stat_block.format(
			"Top 10 articles by page rank:",
			"<br>".join(top_ranked_items))

	def stat_most_citations_made(self):
		"""Computes the top 3 ranks for citations made FROM a page."""
		# Determine which pages are cited from all articles on a page.
		pages_cited = {
			page_title: set()
			for page_title in self.title_to_page.keys()}
		for page_title, articles in self.title_to_page.items():
			for article in articles:
				for citation in article.citations:
					pages_cited[page_title].add(citation.target)
		# Compute the number of unique articles cited by a page.
		for page_title, cite_titles in pages_cited.items():
			pages_cited[page_title] = len(cite_titles)

		# Reverse and itemize the citation counts.
		top_citations = reverse_statistics_dict(pages_cited)[:3]
		top_citations_items = itemize(top_citations)

		# Format the statistics block.
		return self.stat_block.format(
			"Cited the most pages:",
			"<br>".join(top_citations_items))

	def stat_most_citations_to(self):
		"""Computes the top 3 ranks for citations made TO a page."""
		# Determine which pages cite a page.
		pages_cited_by = {
			page_title: set()
			for page_title in self.title_to_page.keys()}
		for page_title, articles in self.title_to_page.items():
			for article in articles:
				for citation in article.citations:
					pages_cited_by[citation.target].add(page_title)
		# Compute the number of unique articles that cite a page.
		for page_title, cite_titles in pages_cited_by.items():
			pages_cited_by[page_title] = len(cite_titles)

		# Reverse and itemize the citation counts.
		top_cited = reverse_statistics_dict(pages_cited_by)[:3]
		top_cited_items = itemize(top_cited)

		# Format the statistics block.
		return self.stat_block.format(
			"Cited by the most pages:",
			"<br>".join(top_cited_items))

	def stat_longest_article(self):
		"""Computes the top 3 longest articles."""
		# Compute the length of each article (not page).
		title_to_article_length = {}
		for article_title, article in self.title_to_article.items():
			# Write all citation aliases into the article text to accurately
			# compute word count as written.
			format_map = {
				"c"+str(c.id): c.text
				for c in article.citations
			}
			plain_content = article.content.format(**format_map)
			word_count = len(plain_content.split())
			title_to_article_length[article_title] = word_count

		# Reverse and itemize the article lengths.
		top_length = reverse_statistics_dict(title_to_article_length)[:3]
		top_length_items = itemize(top_length)

		# Format the statistics block.
		return self.stat_block.format(
			"Longest articles:",
			"<br>".join(top_length_items))

	def stat_cumulative_wordcount(self):
		"""Computes the cumulative word count of the lexicon."""
		# Initialize all extant turns to 0.
		turn_to_cumulative_wordcount = {
			turn_num: 0
			for turn_num in range(self.min_turn, self.max_turn + 1)
		}
		for article_title, article in self.title_to_article.items():
			# Compute each article's word count.
			format_map = {
				"c"+str(c.id): c.text
				for c in article.citations
			}
			plain_content = article.content.format(**format_map)
			word_count = len(plain_content.split())
			# Add the word count to each turn the article exists in.
			for turn_num in range(self.min_turn, self.max_turn + 1):
				if article.turn <= turn_num:
					turn_to_cumulative_wordcount[turn_num] += word_count

		# Format the statistics block.
		len_list = [(str(k), [str(v)]) for k,v in turn_to_cumulative_wordcount.items()]
		return self.stat_block.format(
			"Aggregate word count by turn:",
			"<br>".join(itemize(len_list)))

	def stat_player_pagerank(self):
		"""Computes each player's share of the lexicon's pagerank scores."""
		self._try_populate_pagerank()

		if not self.title_to_pagerank:
			# If networkx was not successfully imported, skip the pagerank.
			player_rank_items = "networkx must be installed to compute pageranks."

		else:
			player_to_pagerank = {
				player: 0
				for player in self.players}
			# Accumulate page pagerank to the main article's author.
			for page_title, articles in self.title_to_page.items():
				page_author = articles[0].player
				if page_author is not None:
					player_to_pagerank[page_author] += self.title_to_pagerank[page_title]
			# Round pageranks off to 3 decimal places.
			for player, pagerank in player_to_pagerank.items():
				player_to_pagerank[player] = round(pagerank, 3)

			# Reverse and itemize the aggregated pageranks.
			player_rank = reverse_statistics_dict(player_to_pagerank)
			player_rank_items = itemize(player_rank)

		# Format the statistics block.
		return self.stat_block.format(
			"Player aggregate page rank:",
			"<br>".join(player_rank_items))

	def stat_player_citations_made(self):
		"""Computes the total number of citations made BY each player."""
		pages_cited_by_player = {
			player: 0
			for player in self.players}
		# Add the number of citations from each authored article (not page).
		for article_title, article in self.title_to_article.items():
			if article.player is not None:
				pages_cited_by_player[article.player] += len(article.citations)

		# Reverse and itemize the counts.
		player_cites_made_ranks = reverse_statistics_dict(pages_cited_by_player)
		player_cites_made_items = itemize(player_cites_made_ranks)

		# Format the statistics block.
		return self.stat_block.format(
			"Citations made by player:",
			"<br>".join(player_cites_made_items))

	def stat_player_citations_to(self):
		"""Computes the total number of citations made TO each player's
		authored pages."""
		pages_cited_by_by_player = {
			player: 0
			for player in self.players}
		# Add the number of citations made to each page (not article).
		for page_title, articles in self.title_to_page.items():
			page_author = articles[0].player
			if page_author is not None:
				pages_cited_by_by_player[page_author] += len(articles[0].citedby)

		# Reverse and itemize the results.
		cited_times_ranked = reverse_statistics_dict(pages_cited_by_by_player)
		cited_times_items = itemize(cited_times_ranked)

		# Format the statistics block.
		return self.stat_block.format(
			"Citations made to article by player:",
			"<br>".join(cited_times_items))

	def stat_bottom_pagerank(self):
		"""Computes the bottom 10 pages by pagerank."""
		self._try_populate_pagerank()

		if not self.title_to_pagerank:
			# If networkx was not successfully imported, skip the pagerank.
			bot_ranked_items = "networkx must be installed to compute pageranks."

		else:
			# Phantoms have no pagerank, because they don't cite anything.
			exclude = [
				a.title
				for a in self.articles
				if a.player is None]
			rank_by_written_only = {
				k:v
				for k,v in self.title_to_pagerank.items()
				if k not in exclude}
			
			# Reverse, enumerate, and itemize the bottom 10 by pagerank.
			pageranks = reverse_statistics_dict(rank_by_written_only)
			bot_ranked = list(enumerate(map(lambda x: x[1], pageranks), start=1))[-10:]
			bot_ranked_items = itemize(bot_ranked)

		# Format the statistics block.
		return self.stat_block.format(
			"Bottom 10 articles by page rank:",
			"<br>".join(bot_ranked_items))

	def stat_undercited(self):
		"""Computes which articles have 0 or 1 citations made to them."""
		undercited = {
			page_title: len(articles[0].citedby)
			for page_title, articles in self.title_to_page.items()
			if len(articles[0].citedby) < 2}
		undercited_items = itemize(reverse_statistics_dict(undercited))
		return self.stat_block.format(
			"Undercited articles:",
			"<br>".join(undercited_items))
