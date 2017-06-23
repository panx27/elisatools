require 'nokogiri'
require 'sequel'
require 'yaml'
module LDC
  module Text
    class Tokenizer
    end
  end
end
require_relative 'tokenization_string_mixin'
require_relative 'tokenizer_word'
require_relative 'tokenizer_char'
require_relative 'tokenizer_punct'
require_relative 'tokenizer_whitespace'
module LDC
  module Text
    class Tokenizer

      attr_accessor :tokenization_filename, :whitespace
      attr_reader :tokenization_parameters

      def tokenization_parameters=(parameters={})
        @tokenization_parameters = parameters
        @patterns = @tokenization_parameters[:patterns]
        @recursive = @tokenization_parameters[:recursive_types]
      end

      def word_tokenizer
        @@word_tokenizer ||= TokenizerWord.new
      end

      def char_tokenizer
        @@char_tokenizer ||= TokenizerChar.new
      end

      def whitespace_tokenizer
        @@whitespace_tokenizer ||= TokenizerWhitespace.new
      end

      def punct_tokenizer
        @@punct_tokenizer ||= TokenizerPunct.new
      end

      def token_count(string, lang=nil)
        tokens(string, lang).count
      end

      def tokens(string, lang=nil)
        raise "tokenization parameters haven't been set" unless @tokenization_parameters
        if @tokenization_parameters[:preprocessor] == :xml
          Nokogiri::XML(string).css('div').inject([]) do |array, div|
            lang = div.attr('lang').to_sym
            array.concat tokenize_by_language(div.text, lang)
          end
        else
          case @tokenization_parameters[:tokenizer]
          when :characters
            char_tokenizer.tokenize string
          when :words
            word_tokenizer.tokenize string
          when :punctuation
            punct_tokenizer.tokenize string
          when :patterns
            tokenize string
          when :by_lang
            tokenize_by_language string, lang
          else
            raise "bad tokenizer: #{@tokenization_parameters[:tokenizer]}"
          end
        end
      end

      def calculate_offsets_from_complete_tokenization(string, tokens)
        # assumes all non-whitespace characters are present
        offset = 0
        tokens.map do |token|
          while string[offset] =~ /\s/
            offset += 1
          end
          token_offset = offset
          offset += token.length
          raise "calculation error" unless token == string.slice(token_offset, token.length)
          [ token, 'unknown', token_offset, token.length ]
        end
      end

      def init_from_yaml_file(fn)
        @tokenization_filename = File.basename fn, '.yaml'
        self.tokenization_parameters = YAML.load File.read fn
      end

      # used to calculate word counts for English and Arabic
      def tokenize_by_words(s)
        word_tokenizer.tokens(s).map(&:first)
      end

      # used to calculate word counts for Chinese
      def tokenize_by_characters(s)
        # s.scan(/\p{Word}/)
        char_tokenizer.tokens(s).map(&:first)
      end

      # this will preserve punctuation in the token stream
      def tokenize_by_punctuation(s)
        # s.scan(/\p{Word}+|\p{Punct}+/)
        punct_tokenizer.tokens(s).map(&:first)
      end

      def tokenize_by_language(s, lang)
        case lang
        when :eng, :arz, :arb, 'English', 'Arabic', 'French'
          tokenize_by_words s
        when :cmn, 'Chinese', 'Mandarin'
          tokenize_by_characters s
        else
          raise "unknown language: #{lang}"
        end
      end

      # produces 4-tuples representing tokens
      # [ token, type, offset, length ]
      # whitespace is an automatic token delimeter
      # strings that don't match a pattern aren't returned
      def tokenize(s)
        # @tokenization_parameters ||= { tokenizer: :patterns, patterns: patterns }
        # set_patterns
        goffset = 0
        tokens = []
        @whitespace = []
        whitespace_tokenizer.tokenize_by_complementary_patterns(s, goffset).each do |token|
        # s.scan(/\s+|\S+/).each do |string|
          # if string[0] =~ /\S/
          if token[1] == 'S'
            tokens.concat match_once token[0], goffset
          else
            whitespace << token if @whitespace
          end
          goffset += token[3]
        end
        tokens
      end



      def tokenize_by_complementary_patterns(s, goffset)
        tokens = []
        while s.length > 0
          token = match_once(s, goffset).first
          raise "complementary scan should have found a match" if token.nil?
          tokens << token
          goffset += token[3]
          s = s[token[3]..-1]
        end
        tokens
      end

      private

      # match once, possibly recursively.  returns an array of quads
      def match_once(string, goffset)
        t = match_patterns string
        if t
          t.each { |x| x[2] += goffset }
          t
        else
          []
        end
      end

      # tries to match all patterns, breaking on first successful match
      def match_patterns(string)
        @patterns.each do |pattern, types|
          token = match_pattern string, pattern, types
          return token if token
        end
        nil
      end

      # matches one pattern if possible
      def match_pattern(string, pattern, types)
        if string =~ pattern

          # if parentheses are used, the first capture is ignored
          # this means the code is most clear when split by this condition

          if $~.size == 1 # no parentheses
            boffset, eoffset = $~.offset 0
            [ [ $~[0], types, boffset, eoffset - boffset ] ]
          else # parentheses
            if types.nil?
              types = Array.new $~.size - 1
            else
              types = types.split
            end
            raise 'length mismatch' unless $~.size - 1 == types.length
            i = 1
            tokens = []
            while i < $~.size
              boffset, eoffset = $~.offset i
              if @recursive and @recursive.include? types[i-1]
                tokens.concat match_once $~[i], boffset
              else
                tokens << [ $~[i], types[i-1], boffset, eoffset - boffset ]
              end
              i += 1
            end
            tokens
          end
        end
      end
    end
  end
end
