# Lexipython

Lexipython is a Python suite for playing Lexicon, a collaborative, worldbuilding, role-playing game.

## Summary

Lexicon is basically _Wikipedia: The RPG_. Each player takes on the role of a scholar. You are cranky, opinionated, prejudiced, and eccentric. You are also collaborating with a number of your peers -- the other players -- on the construction of an encyclopedia describing some bounded space, such as a fantastic world or a historical period. Each round, each scholar contributes an article on a particular topic, citing other articles in the burgeoning encyclopedia. Some of the cited articles won't exist at the time they're cited. As the game progresses, the other scholars will fill in the phantom citations you've made, and you will fill in theirs -- after all, it is an academic sin to cite yourself. Each new article, however, cannot contradict what has already been written: though your peers are self-important, narrow-minded dunderheads, they are honest scholars. No matter how strained their interpretations are, their facts are as accurate as historical research can make them.

## Lexicon and Lexipython

To play Lexicon, all you really need is something for the scholars to write their articles on and a place to collect them. However, if people with doctorates are known for anything, it's their terrible handwriting and disorganization. Lexipython therefore provides tools to solve these most ancient of problems. To play Lexicon with Lexipython, appoint a player or a third party as the game master (GM). The GM will need to download Lexipython, set up the game, and handle posting the pages somewhere all the players can access them.

To aid the GM in running the Lexicon game, Lexipython **does** provide:
* Specialized markdown parsing into formatted lexicon entries
* Page generation and interlinking
* Handy help pages for rules, session information, statistics, and more.

Lexipython **does not** provide:
* Web hosting for the Lexicon pages
* Checks for factual consistency between submitted articles

## Playing Lexicon

1. At the beginning of the game, you will be provided with a _topic statement_ that sets the tone for the game. Use it for inspiration and a stepping-stone into shaping the world of the Lexicon.

1. Each round, you will be assigned an _index_, a grouping of letters. Your entry must alphabetize under that index.

   1. Each index has a number of open slots equal to the number of players, which are taken up by article titles when an article is written in that index or a citation is made to an unwritten article, or _phantom_. If there are no open slots in your index, you must write the article for a phantom in that index.

   1. "The" and "A" aren't counted in indexing.

1. Once you've picked an article title, write your article on that subject.

   1. There are no hard and fast rules about style. Try to sound like an encyclopedia entry or the overview section at the top of a wiki article.

   1. Aim for around 200-300 words.

   1. You must respect and not contradict any factual content of any posted articles. You may introduce new facts that place things in a new light, provide alternative interpretations, or flesh out unexplained details in unexpected ways; but you must not _contradict_ what has been previously established as fact. Use the "Yes, And" rule from improv: accept what your fellow scholars write and add to it, rather than trying to work around them.

1. Your article must cite other articles in the Lexicon. Sometimes these citations will be to phantoms, articles that have not been written yet.

   1. On the first turn, your article must cite _exactly two_ phantom articles.

   1. On subsequent turns, your article must cite _exactly two_ phantom articles, either already-cited phantoms or new ones. Your article must also cite _at least one_ written article.

   1. On the penultimate turn, you must cite _exactly one_ phantom article and _at least two_ written articles.

   1. On the final turn, you must cite _at least three_ written articles.

   1. You may not cite an entry you wrote. You may cite phantoms you have cited before.

   1. Once you cite a phantom, you cannot choose to write it if you write an article for that index later.

**Ersatz Scrivener.** In the course of the game, it may come to pass that a scholar is assigned an index in which no slots are available, because this scholar has already cited all the phantoms in previous articles. When this happens, the player instead writes their article as Ersatz Scrivener, radical skeptic. Ersatz does not believe in the existence of whatever he is writing about, no matter how obvious it seems to others or how central it is in the developing history of the world. All references, testimony, etc. with regard to its existence are tragic delusion at best or malicious lies at worst. Unlike the other scholars, Ersatz does not treat the research of his peers as fact, because he does not believe he has peers. Players writing articles as Ersatz are encouraged to name and shame the work of the misguided amateurs collaborating with him.

## Running Lexicon

**Topic statement.** The GM should pick an appropriate topic statement for the Lexicon. This topic should be vague, but give the players something to start with, such as "You are all revisionist scholars from the Paleotechnic Era arguing about how the Void Ghost Rebellion led to the overthrow of the cyber-gnostic theocracy and the establishment of the Third Republic" or "In the wake of the Quartile Reformation, you are scholars investigating the influence of Remigrationism on the Disquietists". What happened to the first two Republics or what Remigrationism is are unknown at the beginning; they are named to evoke a mood and inspire creativity.

**Indices and turns.** Each turn, the GM will assign each player to write in a certain index. An index is a subset of however entries are sorted. By default, index by letter or by a group of letters. The GM should decide how many turns the game will last and divide up the entry space into that many indices. Each player will take one turn in each index. The suggested index count is 8, dividing the alphabet into the indices ABC, DEF, GHI, JKL, MNO, PQRS, TUV, WXYZ.

The GM should also decide how long players will have to write their article for each turn. At one turn per day, it will take about a week to finish an 8-turn game. Avoid letting too long go between turns, or players may forget what was going on in the Lexicon.

Unless the players have a method of coordinating who is writing what article, it may be useful to always assign players to different indices. The easiest way to do this is to initially distribute players randomly across all indices and have them move through the index list in order, wrapping around to the top from the bottom.

**Varying the rules.** The GM is free to alter the game procedures in service of the goal of the game. By default, articles are indexed alphabetically into 8 indices. A longer game might split the alphabet into 13 pairs. An alternative indexing might index by date over a historical period or some other quality. By default, players move through the index list in order. An alternative might assign the order of indices randomly. In a variation called _Follow the Phantoms_, players can choose what index they write in, but they must always write a phantom article after the first turn. In some circumstances, two players may both have to write an Ersatz article but could write an article in the other's index. The GM might swap the index assignments of such players.

**Additional responsibilities.** Lexipython will generate browsable static HTML files. The GM is responsible for making these generated pages available to the players by hosting or otherwise making the pages available after each round's articles have been turned in and generated. The GM is also responsible for reviewing each round's articles and ensuring that the submitted articles do not contradict each other or the previously written articles.

## Using Lexipython (WIP)

## Acknowledgements

The first version of Lexicon was posted by Neel Krishnaswami on The 20' by 20' Room in 2003. It was inspired by, and named in honor of, Milorad Pavic's _Dictionary of the Khazars: A Lexicon Novel_. The rules were later given some minor clarifications and expansion by Alexander Cherry and posted on Twisted Confessions in 2010. The rules described here were adapted mostly from the 2010 version and revised by Tim Van Baak in 2017.

Special thanks to the scholars of Lexicon Alpha and Lexicon Proximum for their contributions and feedback.
