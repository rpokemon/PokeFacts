# PokeFacts

PokeFacts is a Reddit bot made by the moderators of /r/pokemon
which responds with info about a Pokemon when requested.

(Bot is still in development, not active)

It currently runs on the following subreddits: /r/pokemon

## Usage

In your comment or selfposts, use any of the following: 
{PokemonName}, <PokemonName>, or !PokemonName

Example comment:

    {Bulbsaur} is pretty cool.

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

### Requirements to run

Requires PRAW and Python 3. Using the latest versions is recommended.
If you'd like to test it out for yourself, you'll need to configure the
`PokeFacts/Config.py` and create a `PokeFacts/Secrets.py` file containing
two variables: `PASSWORD` and `APP_SECRET` which are respectively the reddit
account password and OAuth app secret.

### Testing

Run `python runtests.py` to run the tests. Requires pyflakes and pytest.

    pip install -U pytest
    pip install -U pyflakes

It'll run all test files in the `tests/` directory in the format of
`test_*.py` or `*_test.py`.