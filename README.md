# Lexipython

Lexipython is a Python suite for playing Lexicon, a collaborative, worldbuilding, role-playing game. This document explains the game of Lexicon. For documentation of Lexipython, see the [usage readme](LEXIPYTHON.md).

## Summary: If Wikipedia Were an RPG

In Lexicon, each player takes on the role of a scholar. You are cranky, opinionated, prejudiced, and eccentric. You are also collaborating with a number of your peers (the other players) on the construction of an encyclopedia describing some bounded space, such as a fantastic world or a historical period. Each turn, you will write an article on a particular topic, which will cite other, related articles within the burgeoning encyclopedia. This process is complicated by three factors. First, some of the articles you cite will not actually exist at the time you cite them. Second, it is an academic sin to cite yourself. Third, your article may not contradict anything that has already been written. Though your peers are self-important, narrow-minded dunderheads, they are honest scholars. No matter how strained their interpretations are, their facts are as accurate as historical research can make them.

## Basic Rules: What Everyone Should Know

1. Each Lexicon has a _topic statement_ that sets the tone for the game. It provides a starting point for shaping the developing world of the Lexicon. As it is a starting point, don't feel contrained to write only about the topics mentioned directly in it.

1. Articles are sorted under an _index_, a grouping of letters. An article is in an index if its first letter is in that group of letters. "The", "A", and "An" aren't counted in indexing.  _Example: One of the indices is JKL. An article titled 'The Jabberwock' would index under JKL, not T's index._

    1. Until the game is over, some of the articles will have been cited, but not yet written. These are called _phantom_ articles. A phantom article has a title, which is defined by the first citation to it, but no content.

    1. Generally, an index has a number of "slots" equal to the number of players. When an article is first written or cited, it takes up one slot in its corresponding index.

1. Each turn, you will be assigned to write in an index.

    1. Your articles should be written from the perspective of your character. Your character should be a scholar collaborating with the other scholars on the production of the Lexicon. You should play the same character for the duration of the game.

    1. If the index has open slots, you may come up with a new article title and write an article under that title. If all unwritten slots in your index are filled by phantom articles, you must choose one of them and write it.

    1. There are no hard and fast rules about style, but it is recommended that players imitate an encyclopedic style to stay true to the game's conceit.

    1. There are no hard and fast rules about length, but it is recommended that the Editor enforce a maximum word limit. In general, aiming for 200-300 words is ideal.

    1. You must respect and not contradict the factual content of all written articles. You may introduce new facts that put things in a new light, provide alternative interpretations, or flesh out unexplained details in unexpected ways; but you must not _contradict_ what has been previously established as fact. Use the "yes, and" rule from improv acting: accept what your fellow scholars have written and add to it in new ways, rather than trying to undo their work. This rule includes facts that have been established in written articles about the topics of phantom articles.

1. Each article will cite other articles in the Lexicon.

    1. You may not cite an entry that you have written. When you write an article, you may not cite it in later articles.

    1. As a corollary, you may not write phantom articles that you have cited. If you cite an article and then write it later, your former article now cites you, which is forbidden per the above.

    1. On the first turn, there are no written articles. Your first article must cite _exactly two_ phantom articles.

    1. On subsequent turns, your article must cite _exactly two_ phantoms, but you can cite phantoms that already exist. Your article must also cite _at least one_ written article. You can cite more than one.

    1. On the penultimate turn, you must cite _exactly one_ phantom article and _at least two_ written articles.

    1. On the final turn, you must cite _at least three_ written articles.

1. As the game goes on, it may come to pass that a player must write an article in an index, but that index is full, and that player has already cited all the phantoms in it. When this happens, the player instead writes their article as **Ersatz Scrivener**, radical skeptic. Ersatz does not believe in the existence of whatever he is writing about, no matter how obvious it seems to others or how central it is in the developing history of the world. For Ersatz, all references, testimony, etc. with regard to its existence are tragic delusion at best or malicious lies at worst. Unlike the other scholars, Ersatz does not treat the research of his peers as fact, because he does not believe he has peers. Players writing articles as Ersatz are encouraged to lambast the amateur work of his misguided "collaborators".

## Procedural Rules: Running the Game

### The Editor

The player running the game is the Editor. The Editor should handle the following:
* Reading the [usage readme](LEXIPYTHON.md) and configuring Lexipython for the Lexicon game.
* Arranging for making the Lexicon available to all players. (GitHub Pages is an easy solution, and you're already here.)
* Setting the tone for the game, including choosing a topic statement, a logo image, and any other constraints on the flavor of the game.
* Determining other game parameters, such as how many indices there are and how long players will have to write each turn.
* Ensuring that submitted articles do not contradict what has already been established as fact.
* Ensuring that players submit their articles on time.

### Game Parameters

* **Topic statement.** The topic statement should be vague, but give the players some hooks to begin writing. Examples: "You are all revisionist scholars from the Paleotechnic Era arguing about how the Void Ghost Rebellion led to the overthrow of the cyber-gnostic theocracy and the establishment of the Third Republic"; "In the wake of the Quartile Reformation, you are scholars investigating the influence of Remigrationism on the Disquietists". What happened to the first two Republics or what Remigrationism is are left open for the players to determine.

* **Indices and turns.** In general, the Editor will decide on a number of turns and divide the alphabet into that many indices. Each player then takes one turn in each index. A game of 6 or 8 turns is suggested. _Example: An 8-turn game over the indices ABC/DEF/GHI/JKL/MNO/PQRS/TUV/QXYZ._ The Editor should determine how much time the players can devote to playing Lexicon and set a time limit on turns accordingly.

* **Index assignments.** Each turn, the Editor should assign each player to an index. Unless players have a method of coordinating who is writing what article, it is suggested that the Editor always assign players to write in different indices. The easiest way to do this is to distribute players randomly across the indices for the first turn, then move them through the indices in order, wrapping around to the top from the bottom.

### Stylistic Considerations

How the game develops is entirely up to the players, and your group may have a different "meta" concerning how they normally play it out. Here are some miscellanea to keep in mind:

* Some encyclopedias in real life will put an important part of the title in front, so as to alphabetize by a word other than the technically first. This common with the names of persons, resulting in titles like "Lastname, Firstname Q." Players should either stick to this, or avoid it, since it reads oddly to have some titles alphabetized by a last name and others by whatever adjective is in front.

* While it can be fun to write a long article that ties many disparate parts of the Lexicon world together, article length creep can make the amount of content in the Lexicon difficult to keep up with. Additionally, as articles grow longer, they tend to have more citations, which results in more articles being relevant to a particular topic, which in turn makes writing on that topic harder to research to avoid contradictions.

* Even if articles don't get too long, having too many articles on one subject can lead to the same problem of writing on the topic becoming too hard to do consistently. Avoid having multiple articles about the same thing, and avoid having too many articles about different facets of one particular element of the world.

* Encyclopedias are written about things in the past. Players may, of course, want to mention how something in the past still affects the world in the present day. However, if players begin to write about purely contemporary things or events, the Lexicon shifts from an _encyclopedic_ work to a _narrative_ one. If that's what you want out of the game, go ahead and do so, but writing about an ongoing narrative insead of settled history introduce the additional complication of keeping abreast of the current state of the plot. It is more difficult for players to avoid contradiction when the facts are changing as they write.

* Articles whose titles do not begin with a character in any index pattern are sorted to the "&c" index. This usually includes numbers and symbols. If the Editor wants to make purposive use of this, they can assign players to it as an index.

### Rule Variants

The Editor is always free to alter the game procedures when it would make for a better game. The following are some known rule variations:

* **Follow the Phantoms:** Players make two phantom citations on the first turn. On subsequent turns, rather than choosing from phantoms and open slots in an assigned index, players must write an existing phantom. Until all slots are full, players must make one of their phantom citations to a new phantom article and one to an existing phantom.

* Occasionally, if more players make a citation to an index than there are open slots, the index will be over capacity. If the Editor is assigning players to indices in order, the Editor may need to shift players' index assignments around. This may also be useful for decreasing the number of Ersatz articles, if a player can't write in their assigned index but could write in another.

## Acknowledgements

The first version of Lexicon was posted by Neel Krishnaswami on The 20' by 20' Room in 2003. It was inspired by, and named in honor of, Milorad Pavic's _Dictionary of the Khazars: A Lexicon Novel_. The rules were later given some minor clarifications and expansion by Alexander Cherry and posted on Twisted Confessions in 2010. The rules described here were adapted mostly from the 2010 version and revised by Tim Van Baak in 2017-2018.

Special thanks to the scholars of Lexicon Alpha and Lexicon Proximum for their contributions and feedback.
