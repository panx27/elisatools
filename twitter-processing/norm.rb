# Public: Normalize white spaces in a string. Remove leasing and trailing
# spaces and combine sequence of interior spaces into a single space. Also
# handles unicode spaces (e.g. 0xFEFF) that are not captured by \p{Space}.
#
# s - A string.
#
# Returns a normalized string.
def normsp(s)
    s.sub(/^(?:\uFEFF|\p{Space})*/, '').sub(/(?:\uFEFF|\p{Space})*$/,'').gsub(/(?:\uFEFF|\p{Space})+/, ' ')
end

# Public: Divide text into paragraphs. Paragraphs are simply substrings
# divided by 2 or more line breaks.
#
# text - A string.
#
# Returns an array of strings.
def text_to_paras(text)
    text.split(/[\r\n]+/).map do |line|
        normsp line
    end .select {|line| line.size > 0} .join("\n")
end
