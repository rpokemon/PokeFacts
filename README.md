# PokeFacts

PokeFacts is a Reddit bot made by the moderators of /r/pokemon
which responds with info about a Pokemon when requested.

It currently runs on the following subreddits: /r/pokemon

## Usage

In your comment or selfposts, use any of the following: 
{NameHere}, <NameHere>, or !NameHere

The name can be that of any Pokemon, item, ability or move.

Please note that the exclamation mark notation does not work
with names containing spaces. So !Mr. Mime, !Life Orb, !Flame Body
etc won't work, but {Mr. Mime}, {Life Orb}, {Flame Body} etc will.

Example comment:

    {Bulbasaur} is pretty cool.

The bot will attempt to correction spelling mistakes, so {Bulbasaur}
and {Bulsaur} will both work.

## FAQ

### What subreddits does PokeFacts operate on?

Right now, only /r/pokemon.

### I made a mistake, how do I get my comment reprocessed?

In subreddits PokeFacts mods on, you can just edit your comment and it'll
reprocess it.

On subreddits PokeFacts does not mod on, in your edit you must mention PokeFacts
like this: /u/PokeFacts

PokeFacts can also respond to requests outside of the listed subreddits up above
if you mention PokeFacts in the comment.

### The bot replied to me, but some of the information is wrong/missing?

Click on the "Mistake?" link at the bottom of comment, it'll open a page
to send a PM to us. Add any additional information you want and just hit
send and we'll get it fixed!

### The bot didn't reply to me at all. Why?

You might've either made an error with the syntax or the bot had a hiccup.
If you have any concerns, feel free to modmail us at /r/pokemon!

### Who made this bot?

The moderators of /r/pokemon!

## Contributing

### Correcting errata/missing information

The information used by bot are located in `PokeFacts/data/pokemon.json`,
`PokeFacts/data/items.json`, `PokeFacts/data/moves.json`, and `PokeFacts/data/abilities.json`.
Feel free to submit a pull request if you know how, or otherwise submit an issue
or [modmail us on Reddit](https://www.reddit.com/message/compose?to=%2Fr%2Fpokemon).

### Requirements to run

Requires PRAW, Python 3, and psutil. Using the latest versions is recommended.
If you'd like to test it out for yourself, you'll need to configure the
`PokeFacts/Config.py` and create a `PokeFacts/Secrets.py` file containing
two variables: `PASSWORD` and `APP_SECRET` which are respectively the reddit
account password and OAuth app secret.

If you'd like to modify the code to use for your own subreddit, the only
files you need to change are `PokeFacts/Responder.py` and `PokeFacts/Config.py`.
The rest of the code is pretty general. The `Responder.py` file only needs the
`getResponse(item, is_last)` function where 'item' is a DataPulls.Item object.

### Testing

Run `python runtests.py` to run the tests. Requires pyflakes and pytest.

    pip install -U pytest
    pip install -U pyflakes

It'll run all test files in the `tests/` directory in the format of
`test_*.py` or `*_test.py`.