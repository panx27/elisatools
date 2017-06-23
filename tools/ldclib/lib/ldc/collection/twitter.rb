require 'twitter'
require_relative '../text/string_mixin'
module LDC
  module Collection
    class Twitter

      attr_reader :client

      def initialize(keys:, lang: nil)
        if lang
          case lang
          when 'uzb'
            require_relative '../text/lang/uzbek'
            @encoding = LDC::Text::Lang::Uzbek::Encoding.new
          when 'tur'
            require_relative '../text/lang/turkish'
            @encoding = LDC::Text::Lang::Turkish::Encoding.new
          when 'hau'
            require_relative '../text/lang/hausa'
            @encoding = LDC::Text::Lang::Hausa::Encoding.new
          when 'amh'
            require_relative '../text/lang/amharic'
            @encoding = LDC::Text::Lang::Amharic::Encoding.new
          when 'som'
            require_relative '../text/lang/somali'
            @encoding = LDC::Text::Lang::Somali::Encoding.new
          when 'ara', 'fas'
            require_relative '../text/lang/arabic'
            @encoding = LDC::Text::Lang::Arabic::Encoding.new
          when 'cmn', 'rus', 'hun', 'vie', 'spa', 'eng', 'yor'
            "no op"
          else
            raise "unknown language: #{lang}"
          end
        end
        @client = ::Twitter::REST::Client.new do |config|
          config.consumer_key        ,
          config.consumer_secret     ,
          config.access_token        ,
          config.access_token_secret = keys
        end
      end

      def check_limits
        lim = limits
        h = {}
        h[:rate_limit_status] = lim[:resources][:application][:"/application/rate_limit_status"]
        h[:statuses] = lim[:resources][:statuses][:"/statuses/lookup"]
        if h[:rate_limit_status][:remaining] == 0
          warn "surpisingly, there are no remaining rate_limit_status requests"
          warn "as a precaution, sleep 15 minutes then exit"
          sleep 900
          exit
        end
        @remaining = h[:statuses][:remaining]
        @reset = h[:statuses][:reset]
        h
      end

      def download(out_dir:, lines:, raw: false)
        process_tab_lines lines
        check_limits
        twt_max_ids = 100 # max number of tweet ids allowed by lookup api call
        @id2md5.keys.each_slice(twt_max_ids) do |keys|

          ntries = 0
          begin
            abort "download incomplete" if ntries == 3

            if @remaining > 0
              download_helper keys.size
            else
              t1 = Time.now
              t2 = Time.at @reset
              s = t2 - t1
              warn "no lookups can be made before #{t2}, sleeping for {s} seconds"
              sleep s
              check_limits
              download_helper keys.size
            end

            tweets = client.statuses(*keys)

          rescue ::Twitter::Error => e
            p e
            sleep 5
            ntries += 1
            retry
          end

          tweets.each do |tweet|
            fn, text = process_tweet tweet, raw
            open(File.join(out_dir, fn), 'w') do |f|
              f.puts text
            end
            if $options.json
              open(File.join(out_dir, fn.sub(/(raw|rsd.txt)\z/, 'json')), 'w') do |f|
                f.puts JSON.generate(tweet.attrs)
              end
            end
          end

        end
      end

      private

      def download_helper(n)
        raise "how did remaining get to be < 1?" if @remaining < 1
        @remaining -= 1
        warn "downloading #{n} tweets in one lookup, #{@remaining} lookups remain"
      end

      def process_tab_lines(lines)
        @id2md5 = {}
        @id2name = {}
        lines.each do |line|
          filename, tweet_id, md5 = line.chomp.split("\t")
          @id2md5[tweet_id] = md5
          @id2name[tweet_id] = filename
        end
      end

      def normalize(s)
        @encoding ? @encoding.normalize(s) : s
      end

      def process_text(text, md5)
        ['1', '2'].map do |r|
          t = text.send "unexplained_normalization#{r}"
          t = normalize t
          return t if Digest::MD5.hexdigest(t + "\n") == md5
          warn "using second processing rule"
        end
        warn "all processing rules failed"
      end

      def process_tweet(tweet, raw)
        tweet_id = tweet.id.to_s
        filename = @id2name[tweet_id]
        if (not raw) and (text = process_text tweet.text, @id2md5[tweet_id])
          [ "#{filename}.rsd.txt", text ]
        else
          # warn "checksum mismatch: #{tweet.id}"
          # puts tweet.lang
          [ "#{filename}.raw", tweet.text ]
        end
      # rescue Exception => e
      #   warn "failed to write #{filename}.rsd.txt: #{e}"
      end

      def limits
        ::Twitter::REST::Request.new( client, 'get', '/1.1/application/rate_limit_status.json' ).perform
      end

    end
  end
end

# 
