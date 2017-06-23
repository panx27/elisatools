require 'forwardable'
require 'nokogiri'
require_relative 'string_mixin'
module LDC
  module Text
    class SentXML

      extend Forwardable

      def_delegators :@doc, :rsd, :psm, :stack

      attr_accessor :rsd_name, :psm_name

      def initialize(fn)
        @fn = fn
        @rsd_name = File.basename(fn, '.xml') + '.rsd.txt'
        @psm_name = File.basename(fn, '.xml') + '.psm.xml'
      end

      def parse
        @doc = SaxDoc.new @rsd_name
        open(@fn) do |f|
          Nokogiri::XML::SAX::Parser.new(@doc).parse f
        end
      end

      def parse_string(s)
        @doc = SaxDoc.new @rsd_name
        Nokogiri::XML::SAX::Parser.new(@doc).parse s
      end

      class SaxDoc < Nokogiri::XML::SAX::Document

        attr_reader :rsd, :psm, :stack

        def initialize(rsd_name)
            super()
            @rsd_name = rsd_name
            @stack = []
            @sents = []
            @sent = []
            @pos = 0
            @psm = []
            @inside_seg = false
        end

        def start_element name, attrs=[]
            @stack << {tag:name, pos:@pos, attrs:attrs}
            # if name == "seg"
            if name == "segment"
                @sent = []
                @inside_seg = true
            end
        end

        def end_element name
            case name
            # when "seg"
            when "segment"
                text = @sent.join("").text_to_paras + "\n"
                @sents << text
                @pos += text.size
                @inside_seg = false
            when "p"
                @sents << ["\n"]
                @pos += 1
            end

            o = @stack.pop
            o[:length] = [@pos - o[:pos], 0].max
            @psm << o
        end

        def characters string
            if @inside_seg
                @sent << string
            end
        end

        def end_document
            builder = Nokogiri::XML::Builder.new do |xml|
                xml.psm(:"src-doc" => @rsd_name)  do
                    @psm.each do |o|
                        xml.string :type => o[:tag], :begin_offset => o[:pos], :char_length => o[:length] do
                            o[:attrs].each do |attr|
                                xml.attribute :name => attr[0], :value => attr[1]
                            end
                        end
                    end
                end
            end
            @rsd = @sents.join
            @psm = builder.to_xml(encoding:"utf-8")
        end

      end

    end
  end
end

