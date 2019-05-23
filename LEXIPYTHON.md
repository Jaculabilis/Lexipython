# Lexipython

This document explains the Lexipython suite. For the rules of Lexicon, see the [main readme](README.md).

To play Lexicon, all you really need is something for the scholars to write their articles on and a place to collect them. However, if people with doctorates are known for anything, it's their terrible handwriting and disorganization. Lexipython therefore provides tools to solve this most ancient of problems. To play Lexicon with Lexipython, appoint a player or a third party as the Editor. The Editor will need to download Lexipython, set up the game, and handle posting the pages somewhere all the players can access them.

## Functionality

To aid in playing Lexicon, Lexipython **does** provide the following:
* Specialized markdown parsing into formatted Lexicon entries.
* An editor with a live preview of the parsed result and a download button.
* HTML page generation and interlinking.
* Handy help pages for rules, markdown formatting, session information, and statistics.

Lexipython **does not** provide:
* Programmatic article submission. The current version of Lexipython does not involve a persistent server process. Players must send their articles to the Editor themselves.
* Web hosting for the Lexicon pages. The Editor should have a plan for distributing new editions of the Lexicon, such as GitHub Pages.
* Checks for factual consistency between submitted articles. The Editor is responsible for ensuring scholarly rigor.

## Using Lexipython

To run a game of Lexicon with Lexipython, use [git](https://git-scm.com/) to clone this repository out to a new folder.
```
$ git clone https://github.com/Jaculabilis/Lexipython.git
```

Lexipython requires [Python 3](https://www.python.org/downloads/). It will run with only the Python 3 standard library installed, but pagerank statistics will be unavailable without `networkx` installed.
```
$ pip install --user networkx
```

When you have the necessary software installed, open a terminal in the Lexipython directory. You can view the usage of the program with
```
$ python lexipython -h
usage: lexipython [-h] [name] [command]

Lexipython is a Python application for playing the Lexicon RPG.

positional arguments:
  name        The name of the Lexicon to operate on
  command     The operation to perform on the Lexicon

optional arguments:
  -h, --help  show this help message and exit

Run lexipython.py without arguments to list the extant Lexicons.

Available commands:

    init        Create a Lexicon with the provided name
    build       Build the Lexicon, then exit
    run         Launch a persistent server managing the Lexicon
```

Your lexicons are stored in the `lexicon/` folder. Run `python lexipython` to see the status of all lexicons. Except I haven't implemented that yet. Ignore that bit. If you run `python lexipython [name]`, you'll get the status of the named lexicon. That also hasn't been implemented. Whoops!

To create a lexicon, run `python lexipython [name] init` with the name of the lexicon. A folder will be created in `lexicon/` with the given name and some default files will be copied in. You'll need to add a logo image to the folder and edit the config. As players submit articles, place the .txt files in `lexicon/[name]/src/`.

When you finish your initial edits to the config and whenever you want to update the generated HTML files, run `python lexipython [name] build`. Lexipython will regenerate the article pages under `lexicon/[name]/article/` as well as the contents, formatting, rules, session, and statistics pages, and the editor.

To publish the pages, simply copy the lexicon's folder to wherever you're hosting the static files. If you wish, you can leave out the `src/` directory and the status and cfg files. They're are not navigable from the public-facing pages.

The `run` command isn't implemented yet either, and to be honest that probably isn't how you're supposed to implement it in the first place. Ignore it for now.

## Configuring a lexicon

[`lexicon.cfg`](lexipython/resources/lexicon.cfg) contains comments explaining the various config options. `PROMPT` and `SESSION_PAGE` should be written as raw HTML, and will be inserted directly into the page. If you wish to use the Addendums rule explained in the main readme, set `ALLOW_ADDENDA` to `True`. If `SEARCHABLE_FILE` is defined, then the Session page will link to a file with all the articles on one page.

## Other notes

At the end of the build, Lexipython will check for players citing themselves. The program does not fault on these checks, because players may be writing articles as Ersatz Scrivener, or otherwise allowed to cite themselves. Watch out for any unexpected output here.