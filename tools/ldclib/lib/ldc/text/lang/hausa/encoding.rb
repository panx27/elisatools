module LDC
  module Text
    module Lang
      module Hausa

        class Encoding

# Public: Normalize apostrophe-like punctuation characters to
# "modifier letter apostrophe" when there is both a letter following
# and a letter or digit preceding, or whenever the following letter is
# "[Yy]".  Any single occurrence of \u0027, \u0060, \u2018, \u2019 is
# replaced by \u02bc.
#
# Returns an apostrophe-normalized string

          def normalize_latin( strng )
            apostrophes = "'`\u2018\u2019"
            norm_strng = strng.gsub( /(?<=[\p{Letter}\d])[#{apostrophes}](?=\p{Letter})/, "\u02BC" ).gsub( /[#{apostrophes}](?=[Yy])/, "\u02BC" )
          end

          def normalize(string)
            normalize_latin string
          end

        end

      end
    end
  end
end



