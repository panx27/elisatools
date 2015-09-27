#! /usr/bin/env ruby
#
# Download and normalize tweets (text only).
#
# Usage (example)
#
#   This is just an example. Use -h option to see the full options.
#
#   $ get_tweet_by_id.rb -l uzb < uzbek_tweet_ids_with_checksum.tab
#
# Input
#
#   - Table of output file name, tweet ID and md5 checksum from STDIN. The
#     table may contain more columns which are ignored.
#   - Directory to produce ouput in.
#
# Output
#
#   - RSD (.rsd.txt) files in the specified directory if downloaded an checksum matches.
#   - .raw files in the specified directory if downloaded but checksum is bad.
#   - Log messages in STDERR. Download failures and checksum failures are included.
#
# Files
#
#   - ~/.twitter_api_keys containing 4 lines of strings as follows. These strings can be
#     obtained from twitter developer web site. Use -k option to override the default
#     location.
#
#     * consumer key
#     * consumer secret
#     * access token
#     * access token secret
#
#   - ~/.twitter_api_ts which is used to keep track of when api call is made. Use -t option
#     to override the default location.
#
# Latin transliteration
#
#   - Latin transliteration code is included in this script. Currently only Uzbek Cyrillic
#     script is supported. Use -l option to activate the transliteration.
#

require 'optparse'
require 'twitter'
require 'json'
require 'cgi'
require 'time'
require_relative './norm.rb'

OptionParser.new do |opts|
    opts.banner = "Usage: #{File.basename $0} [options] out_dir <tweet_list"

    opts.on("-k", "--keys [PATH]", "api keys file (default=~/.twitter_api_keys)") do |path|
        CONFIG = path
    end

    opts.on("-t", "--time [PATH]", "timestamp file (default=~/.twitter_api_ts)") do |path|
        CALL_HISTORY = path
    end

    opts.on("-l", "--latin [LANG]", "transliterate source text") do |lang|
        case lang
        when 'uzb'
            require_relative '../encoding/uzb_encoding.rb'
            TR = UzbekEncoding::Transliterator.new
            class <<TR
                def trans(s); normalize_latin(cyrillic_to_latin(s)) end
            end
        else
            warn "transliteration not available for language #{lang.inspect} -- disabled"
        end
    end
end.parse!

OUT_DIR = ARGV[0]
CONFIG = File.expand_path("~/.twitter_api_keys") unless defined? CONFIG
CALL_HISTORY = File.expand_path("~/.twitter_api_ts") unless defined? CALL_HISTORY
TWT_INTERVAL = 900   # length of time window for which rate limit is defined
TWT_MAX = 60         # max number of lookup calls within the inverval
TWT_MAX_IDS = 100    # max number of tweet ids allowed by lookup api call


# Throttles the twitter API calls according the their rate limit.
# Client of the class should wrap each call inside the block given to
# the #exec method.
class RateManager
    def initialize(requests, interval, call_history=CALL_HISTORY)
        @num_req = requests
        @interval = interval
        @ts = if File.exists? call_history
            JSON.parse(File.open(call_history).read).map {|x| Time.parse x}
        else
            []
        end

        c = class <<@ts; self end
        [:<<, :shift, :pop].each do |m|
            c.send(:define_method, m) do |*args|
                super *args
                File.open(call_history, "w") {|f| f.write(self.to_json)}
            end
        end
    end

    def exec()
        loop do
            @ts << Time.now
            @ts.shift while @ts.last - @ts.first > TWT_INTERVAL
            if @ts.count > TWT_MAX
                n = TWT_INTERVAL - (@ts.last - @ts.first) + 1
                @ts.pop
                warn "Rate limit reached. Waiting for #{n} seconds..."
                sleep n
            else
                break
            end
        end
        yield
    end
end


def process_text(text, md5)
    ['', ' '].map do |r|
        t = TR.trans( normsp CGI.unescapeHTML(text).gsub(/[\t\n]/, r) )
        return t if Digest::MD5.hexdigest(t + "\n") == md5
        warn "using second processing rule"
    end
    warn "all processing rules failed"
end


def write_text(filename, text)
    File.open(filename, 'w') do |file|
        file.puts text
    end
end


def process_tweet(tweet, md5, filename)
    if (text = process_text tweet.text, md5)
        write_text File.join(OUT_DIR, "#{filename}.rsd.txt"), text
    else
        warn "checksum mismatch: #{tweet.id}"
        write_text File.join(OUT_DIR, "#{filename}.raw"), tweet.text
    end
rescue Exception => e
    warn "failed to write #{filename}.rsd.txt: #{e}"
end


# Main routine begins

abort "specify output directory" unless OUT_DIR
# warn "using config file: #{CONFIG}"
# warn "using timestamp file: #{CALL_HISTORY}"

begin
    Dir.mkdir OUT_DIR unless Dir.exists? OUT_DIR
rescue
    abort "failed to create the directory: #{OUT_DIR}"
end

# if File.exists? CONFIG
#     lines = File.open(CONFIG).readlines
#     CONSUMER_KEY = lines[0].strip
#     CONSUMER_SECRET = lines[1].strip
#     ACCESS_TOKEN = lines[2].strip
#     ACCESS_TOKEN_SECRET = lines[3].strip
# else
#     abort "config file not found: #{CONFIG}"
# end
CONSUMER_KEY = "NbGWpfFFFIRjPrOgx7a6uZNJm"
CONSUMER_SECRET = "n3lCZFPiSXZARk3wCbK6e0Iraq6Lzn7kfg3z5liqlygqnDp0sC"
ACCESS_TOKEN = "2800010370-Ed5JyZQRSQV0qEzv44b15eMeVub85EHIc08ZFEi"
ACCESS_TOKEN_SECRET = "gzFjM0c69QdBa7GLOAIPNq9ys4YibDaEXni2WkWIn5zly"

TR = Class.new do def trans(s) s end end.new unless defined? TR

client = Twitter::REST::Client.new do |config|
  config.consumer_key        = CONSUMER_KEY
  config.consumer_secret     = CONSUMER_SECRET
  config.access_token        = ACCESS_TOKEN
  config.access_token_secret = ACCESS_TOKEN_SECRET
end


rm = RateManager.new TWT_MAX, TWT_INTERVAL

STDIN.each_slice(TWT_MAX_IDS) do |lines|

    id2md5 = {}
    id2name = {}

    lines.each do |line|
        filename, tweet_id, md5 = line.split("\t")
        id2md5[tweet_id] = md5
        id2name[tweet_id] = filename
    end

    begin
        tweets = rm.exec {client.statuses(*id2md5.keys)}
    rescue Twitter::Error => e
        p e
        sleep 5
        retry
    end

    tweets.each do |tweet|
        tweet_id = tweet.id.to_s
        process_tweet tweet, id2md5[tweet_id], id2name[tweet_id]
    end

    (id2md5.keys - tweets.map(&:id).map(&:to_s)).each do |tid|
        warn "failed to download #{tid}"
    end
end
