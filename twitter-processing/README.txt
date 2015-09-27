Files
-----

get_tweet_by_id.py      Download and normalize tweets.
                        Depends on transliteration code found in the
                        tools/encoding directory.

README.txt              This file.


Prerequisite
------------
The Twitter Ruby Gem
  gem install twitter


(Xiaoman: I hardcode my twitter API Keys in get_tweet_by_id.rb)
You need a twitter API key and an access token to be able to download tweets
from the server. Go to the following URL to create an app.

  https://apps.twitter.com/app/new

Once the app is created, open the "Keys and Access Tokens" tab, which is
linked to a URL like this

  https://apps.twitter.com/app/1234567/show

From the page obtain these:

  - API key
  - API secret
  - access token
  - access token secret

Put those in the following directory on their own line.

  ~/.twitter_api_keys


Usage
-----

Make sure to obtain API key and access token for twitter as described above.

Then, use commands like this

  $ get_tweet_by_id.rb /my_dir < tweets.tab

If transliteration of the source text is required, use -l option.

  $ get_tweet_by_id.rb -l uzb /my_dir < tweets.tab  # Uzbek data requires transliteration

The input to the program is a tab-delimited table.  First column of the input
table should be the file names to be created. Second column is numeric tweet
IDs and the second column is md5 checksums of the tweets. The rest of the
columns are ignored. For each tweet, the program

  - downloads the text,
  - normalizes it, and
  - verifies the md5 checksum.

If everything goes well, an RSD file (with .rsd.txt extension) is created for
the tweet.

If the normalization fails and thus md5 checksum doesn't match with the
provided one, a .raw file is created.

The .raw file cannot be used with accompanied standoff annotation files,
if any, because character offsets are not well aligned.

It's possible that some tweets are no longer available on the server, in such
case download will fail and neither .txt nor .raw file will be created.

-----

Portions (c) 2014 Trustees of the University of Pennsylvania
