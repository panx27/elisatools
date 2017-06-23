require 'cgi'
class String

# from Haejoong's norm.rb

# Public: Normalize all whitespace in a string.  Remove leading and
# trailing whitespace and combine sequences of interior whitespace
# into a single ASCII space (\u0020).  Also handles unicode spaces
# (e.g. 0xFEFF) that are not captured by \p{Space}.
#
# Returns a space-normalized string

  def normsp
    sub(/^(?:\uFEFF|\p{Space})*/, '').sub(/(?:\uFEFF|\p{Space})*$/,'').gsub(/(?:\uFEFF|\p{Space})+/, ' ')
  end

# Applies space-normalization in-place

  def normsp!
    sub!(/^(?:\uFEFF|\p{Space})*/, '').sub!(/(?:\uFEFF|\p{Space})*$/,'').gsub!(/(?:\uFEFF|\p{Space})+/, ' ')
  end

# adapted from Graff's uzb_encoding.rb

# Public: Normalize apostrophe-like punctuation characters to
# "modifier letter apostrophe" when there is both a letter following
# and a letter or digit preceding.  Any single occurrence of four
# variants (\u0027, \u0060, \u2018, \u2019) is replaced by \u02bc
#
# Returns an apostrophe-normalized string

  def normapostrophe
    gsub( /(?<=[\p{Letter}\d])['`\u2018\u2019](?=\p{Letter})/, "\u02BC" )
  end

# Applies apostrophe-normalization in-place

  def normapostrophe!
    gsub!( /(?<=[\p{Letter}\d])['`\u2018\u2019](?=\p{Letter})/, "\u02BC" )
  end

# Public: Divide text into paragraphs. Paragraphs are simply substrings
# divided by 2 or more line breaks.
#
# Returns an array of strings.

  def text_to_paras
    split(/[\r\n]+/).map do |line|
      line.normsp
    end .select {|line| line.size > 0} .join("\n")
  end
  
  def unexplained_normalization1
    unexplained_normalization_helper ''
  end

  def unexplained_normalization2
    unexplained_normalization_helper ' '
  end

  def unexplained_normalization_helper(r)
    CGI.unescapeHTML(self).gsub(/[\t\n]/, r).normsp
  end

end


