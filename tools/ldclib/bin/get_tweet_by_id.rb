#! /usr/bin/env ruby
require 'json'
require 'time'
require 'yaml'
# require_relative './norm.rb'
require_relative '../lib/ldc/ldclib'
require_relative '../lib/ldc/cli'
require_relative '../lib/ldc/collection/twitter'

cli = LDC::CLI.new do |op|
  op.add_to_banner "

#{File.basename $0} -l lang out_dir < tweet_list
#{File.basename $0} -l lang out_dir < tweet_list --json

"
  op.on "k keys:FILE api keys file (default=~/.twitter_api_keys)"
  op.on("l lang:LANG language specific normalization, like transliteration")
  op.on '- raw force raw download (no normalization)'
  op.on '- limits check the api rate limits'
  op.on '- json output json as well'
  op.man File.absolute_path __FILE__
end

abort "please specify a language with -l" unless $options.lang

# assume a particular config file if none is specified, which holds api keys
cli.set_default_file option: :keys, fn: File.expand_path("~/.twitter_api_keys")
cli.check_file_options
keys = File.readlines($options.keys).map(&:chomp)

# directory for files to be created
OUT_DIR = ARGV[0]
cli.check_output_dir OUT_DIR

twitter = LDC::Collection::Twitter.new keys: keys, lang: $options.lang

# check rate limits
if $options.limits
  puts twitter.check_limits.to_yaml
  exit
end

twitter.download out_dir: OUT_DIR, lines: STDIN.readlines, raw: $options.raw

  # (id2md5.keys - tweets.map(&:id).map(&:to_s)).each do |tid|
  #     warn "failed to download #{tid}"
  # end
# end
__END__
get_tweet_by_id.rb(1) -- downloads tweets
================================================

## SYNOPSIS

Download and normalize tweets (text only).

## Usage (example)

  This is just an example. Use -h option to see the full options.

  $ get_tweet_by_id.rb -l lng < lng_tweet_ids_with_checksum.tab

## Input

  - Table of output file name, tweet ID and md5 checksum from STDIN. The
    table may contain more columns which are ignored.
  - Directory to produce ouput in.

## Output

  - RSD (.rsd.txt) files in the specified directory if downloaded and checksum matches.
  - .raw files in the specified directory if downloaded but checksum is bad.
  - Log messages in STDERR. Download failures and checksum failures are included.
  - .json files in parallel if the --json flag is used.

## Files

  - ~/.twitter_api_keys containing 4 lines of strings as follows. These strings can be
    obtained from the twitter developer web site. Use -k option to override the default
    location.

    * consumer key
    * consumer secret
    * access token
    * access token secret

## Authors

  Originally written by Haejoong Lee as a mostly standalone executable, and found
  in the low_resource_language repo.
  Extensively edited by Jonathan Wright when added to ldclib, to generalize, add rspec, etc.
