require 'json'
require_relative 'segment'
require_relative "lang/amharic"
require_relative "lang/somali"
require_relative "lang/arabic"
module LDC
  module Text
    class PassThroughNormalizer
      def normalize(string)
        string
      end
    end
    class Segmenter

      def initialize(type:, lang: nil, segmenter: nil, model: nil)
        @pass_through_normalizer = PassThroughNormalizer.new
        @type = type
        @lang = lang
        case type
        when :punkt
          raise "no lang given" unless @lang
          c = File.join File.dirname(__FILE__), 'sentseg-pipe.py'
          @pipe = IO.popen([c, @lang], "r+")
        when :ldc_sent_seg 
          raise "no segmenter given" unless segmenter
          raise "no model given" unless model
          @pipe = IO.popen([segmenter, model, '--ignore_newlines'], "r+")
        end
      end

      # punkt can't be incorporated, as is, into #segment because it doesn't return offsets
      def segment_with_punkt(string)
        if @lang
          tr = case @lang
          when 'amh'
            LDC::Text::Lang::Amharic::Encoding.new
          when 'som'
            LDC::Text::Lang::Somali::Encoding.new
          when 'ara', 'fas'
            LDC::Text::Lang::Arabic::Encoding.new
          when 'cmn', 'rus', 'hun', 'vie', 'spa', 'eng', 'yor'
            @pass_through_normalizer
          else
            raise "unknown language: #{@lang}"
          end
          string = tr.normalize string
        end
        pass_through_pipe string
      end

      def pass_through_pipe(string)
        @pipe.write JSON.dump(string)
        @pipe.write "\n"
        @pipe.flush
        JSON.load @pipe.readline
      end

      def segment(string)
        segments = []
        case @type
        when :punkt
          raise "must use #segment_with_punkt"
        when :simple
          string.scan(/\S.+?\./m) do
            a, b = $~.offset(0)
            segments << Segment.new( self, a, b - a, $~[0] )
          end
        when :gw
          string.scan(/<P>(.+?)<\/P>/m) do
            a, b = $~.offset(1)
            segments << Segment.new( self, a, b - a, $~[1] )
          end
        when :lines
          string.scan(/.+/) do
            a, b = $~.offset(0)
            segments << Segment.new( self, a, b - a, $~[0] )
          end
        when :single
          segments << Segment.new( self, 0, string.length, string )
        else
          raise "bad segmenter"
        end
        segments
      end

      def punkt(string:, xpath: nil)
        count = 0
        if xpath
          doc = Nokogiri::XML(string)
          texts = doc.xpath(xpath)
          texts.each do |text|
            next if /\A\p{Space}*\Z/m.match(text)
            text.content.split(/[\n\r]{2,}/).each do |para|
              p = doc.create_element "p"
              p.add_child doc.create_text_node("\n")
              segment_with_punkt(para).each do |sent|
                # n = doc.create_element "seg", sent.normsp, :id => "seg-#{count}"
                n = doc.create_element "segment", sent.normsp, :id => "segment-#{count}"
                count += 1
                p.add_child n
                p.add_child doc.create_text_node("\n")
              end
              text.add_previous_sibling p
              p.add_previous_sibling doc.create_text_node("\n")
            end 
            text.content = "\n"
          end
          doc
        else
          Nokogiri::XML::Builder.new do |xml|
            xml.doc_ {
              string.split(/[\r\n]{2,}/).each do |para|
                xml.p {
                  segment_with_punkt(para).each do |sent|
                    # xml.seg(id:"seg-#{count}") {
                    xml.segment(id:"segment-#{count}") {
                      xml.text sent.normsp
                    }
                    count += 1
                  end
                }
              end
            }
          end
        end.to_xml(encoding:"utf-8")
      end

    end
  end
end

