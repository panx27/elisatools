require_relative 'tokenizer'
module LDC
  module Text
    class TokenizerChar < Tokenizer

      def initialize
        self.tokenization_parameters = { 
          tokenizer: :patterns,
          recursive_types: %w[ recursive ],
          patterns: [
            [ /(\p{Word})(.+)/, 'word recursive' ],
            [ /\p{Word}/, 'word' ]
          ]
        }
      end

    end
  end
end
