module LDC
  module Text
    class TokenizerPunct < Tokenizer

      def initialize
        self.tokenization_parameters = { 
          tokenizer: :patterns,
          recursive_types: %w[ recursive ],
          patterns: [
            [ /^(\p{Word}+)([^\p{Word}].*)/, 'word recursive' ],
            [ /^(\p{Punct}+)([^\p{Punct}].*)/, 'punct recursive' ],
            [ /^[^\p{Word}\p{Punct}]+(.+)/, 'recursive' ],
            [ /\p{Word}+/, 'word' ],
            [ /\p{Punct}+/, 'punct' ]
          ]
        }
      end

    end
  end
end
