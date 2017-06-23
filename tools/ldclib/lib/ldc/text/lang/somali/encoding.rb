module LDC
  module Text
    module Lang
      module Somali

        class Encoding

# Public: Normalize apostrophe-like punctuation characters to
# "modifier letter apostrophe" when there is both a letter following
# and a letter or digit preceding.
#
# Returns an apostrophe-normalized string

          def normalize_latin( strng )
            apostrophes = "'`\u2018\u2019"
            norm_strng = strng.gsub( /(?<=[\p{Word}\d])[#{apostrophes}](?=\p{Letter})/, "\u02BC" )
          end

          def normalize(string)
            normalize_latin string
          end

        end

      end
    end
  end
end



