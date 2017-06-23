module LDC
  module Text

    class Token

      attr_accessor :document, :type, :offset, :length, :analysis, :end, :analysis_set, :analyses, :analysis_string

      def initialize(token:, document: nil, type: nil, offset: 0, segment: nil, downcase: true)
        @text = token
        @document = document
        @type = type
        @offset = offset
        @length = token.length
        @end = @offset + @length - 1
        @analysis_string = downcase ? @text.downcase : @text
        @analyses = {}
        #raise "bad token: #{check} #{string}" if check and check != string
      end

      def string
        @text
        # @document.string[@offset..@end]
      end

      def to_quad
        [ string, @type, @offset, @length ]
      end

      def to_quad_token_last
        [ @type, @offset, @length, string ]
      end

      def accept_and_simplify_first_valid
        set = @analysis_set
        @type, @analysis = set.first if set and set.size > 0
        @analysis ||= 'none'
        # if set and set.count > 0
        #   a = set.analyses.keys.first
        #   @analysis = set.analyzer.simplify_and_lemmafy a
        #   @type = set.analyzer.pos a
        # end
        @type = '.' if @type == 'punct'
        @type = 'NUM' if @type.include? 'num'
        @type = 'X' if @type == 'word'
      end

      def analyses_with_strings
        h = {}
        @analyses.each do |analysis, v|
          index = 0
          h[
            analysis.map do |length, m|
              s = string.slice index, length
              as = @analysis_string.slice index, length
              index += length
              [ s, as, m ]
            end
          ] = v
        end
        h
      end

    end

  end

end
