module LDC
  module Text
    class TokenizerWord < Tokenizer

      def initialize
        self.tokenization_parameters = { 
          tokenizer: :patterns,
          recursive_types: %w[ recursive ],
          patterns: [
            [ /(\p{Word}+)([^\p{Word}].*)/, 'word recursive' ],
            [ /\p{Word}+/, 'word' ]
          ]
        }
      end

      def tokenize(s)
        # @tokenization_parameters ||= { tokenizer: :patterns, patterns: patterns }
        # set_patterns
        goffset = 0
        tokens = []
        # whitespace_tokenizer.tokenize_by_complementary_patterns(s, goffset).each do |token|
        # # s.scan(/\s+|\S+/).each do |string|
        #   # if string[0] =~ /\S/
        #   if token[1] == 'S'
        #     tokens.concat match_once token[0], goffset
        #   end
        #   goffset += token[3]
        # end
        s.scan(/\p{Word}+/) do |m|
          tokens << [ m, 'word', $~.offset(0).first, m.length ]
        end
        tokens
      end

    end
  end
end
