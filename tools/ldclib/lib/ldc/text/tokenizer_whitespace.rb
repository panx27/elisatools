module LDC
  module Text
    class TokenizerWhitespace < Tokenizer

      def initialize
        self.tokenization_parameters = { 
          tokenizer: :complementary,
          patterns: [
            [ /^\s+/, 's' ],
            [ /^\S+/, 'S' ]
          ]
        }
      end

    end
  end
end
