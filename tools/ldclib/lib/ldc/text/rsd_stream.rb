require_relative 'stream'
require_relative 'sent_xml'
module LDC
  module Text
    class RSDStream < Stream

      def initialize(segmenter:, xpath:)
        @segmenter = segmenter
        @xpath = xpath
      end

      def run_io(fn, rsd, psm)
        @fn = fn
        input = File.read fn
        # begin
        r, p = create_rsd_psm fn, input
        open(rsd, 'w') { |f| f.puts r }
        open(psm, 'w') { |f| f.puts p }
        # rescue EOFError => e
        #   raise SkipError, fn
        # end
        nil
      end

      def create_rsd_psm(fn, input)
        xml = SentXML.new File.basename(fn)
        xml.rsd_name = File.basename(fn)
        input = @segmenter.punkt( string: input, xpath: @xpath ) if @segmenter # unless input_type == 'sent' # pre-segmented
        xml.parse_string input
        [ xml.rsd, xml.psm ]
      end

    end
  end
end

