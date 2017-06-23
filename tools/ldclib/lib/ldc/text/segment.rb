require_relative 'token'
module LDC
  module Text

    class Segment

      attr_reader :document, :offset, :length, :end
      attr_accessor :tokens, :annotations, :whitespace

      def initialize(document, offset, length, text)
        @document = document
        @offset = offset
        @length = length
        @end = @offset + @length - 1
        @tokens = []
        @text = text
      end

      def string
        @text
        # @document.string[@offset..@end]
      end

      def tokenize(tokenizer)
        @tokens = tokenizer.tokens(string).map do |token|
          Token.new document: @document, type: token[1], offset: token[2] + @offset, token: token[0]
          # Token.new @document, nil, 0 + @offset, 0, token
          # Token.new @document, nil, 0 + @offset, 0, token
        end
        @whitespace = tokenizer.whitespace
=begin
        a = @tokens.map { |x| x.string }.join
        b = string.split.join
        if a != b
          puts 'a:'
          puts a
          puts 'b:'
          puts b
          raise 'bad tokenization'
        end
=end
        @tokens
      end

      def token_quads
        @tokens.map { |x| [ x.string, x.type, x.offset, x.length ] }
      end

      # def accept_unique_valid
      #   @tokens.each do |token|
      #     set = token.analysis_set
      #     token.analysis = set.analyses.keys.first if set and set.count == 1
      #   end
      # end

      # def accept_first_valid
      #   @tokens.each do |token|
      #     set = token.analysis_set
      #     if set and set.count > 1
      #       a = set.select_valid_analyses.first
      #       token.analysis = a
      #       token.type = set.analyzer.pos a
      #     end
      #   end
      # end

      def accept_and_simplify_first_valid
        @tokens.each do |token|
          token.accept_and_simplify_first_valid
        end
      end

      # def fix
      #   @tokens.each do |token|
      #     puts token.analysis
      #   end
      # end

      def include_token?(token)
        @offset <= token.offset and @end >= token.end
      end

    end
  end
end
