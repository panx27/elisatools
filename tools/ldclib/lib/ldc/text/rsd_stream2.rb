require_relative 'rsd_stream'
require_relative 'vacuous_segmenter'
module LDC
  module Text
    class RSDStream2 < RSDStream

      def initialize(segmenter:, xpath:, lang:)
        @segmenter = segmenter
        @xpath = xpath
        @problematic_tags = %w[ a img ]
        @vacuous = VacuousSegmenter.new lang: lang
      end

      def create_rsd_psm(fn, orig_xml)
        xml = SentXML.new File.basename(fn)
        xml.rsd_name = File.basename(fn)
        sent_xml = add_segment_tags_after_removing_problematic_tags orig_xml
        # the parse operation creates the rsd and psm
        xml.parse_string sent_xml
        rsd = xml.rsd
        psm = xml.psm
        psm = add_extra_psm_for_problematic_tags orig_xml, rsd, psm
        [ rsd, psm ]
      end

      # add <segment> tags after first removing problematic tags that can occur mid sentence
      def add_segment_tags_after_removing_problematic_tags(input)
        return input if @segmenter.nil? # must be sent xml
        pat = @problematic_tags.join '|'
        @segmenter.punkt( string: input.gsub(/<\/?(#{pat}).*?>/, ''), xpath: @xpath )
      end

      def add_extra_psm_for_problematic_tags(input, rsd, psm)
        return psm if @segmenter.nil? # must be sent xml
        psm.insert(-8, create_psm_for_problematic_tags(input, rsd))
      end

      def create_psm_for_problematic_tags(input, rsd)
        alignment = OpenStruct.new
        alignment.input = input
        alignment.rsd = rsd
        alignment.rsdp = 0
        alignment.stack = []
        alignment.output = []
        input.scan(/<.+?>|[^<>]+/m).each do |x|
          align_step x, alignment
        end
        if alignment.stack.size > 0
          puts alignment.stack
          raise "stack not empty"
        end
        s = alignment.output.map do |span|
          next unless @problematic_tags.include? span.tag
          if span.atts and span.atts.length > 0
            [
              "  <string type=\"#{span.tag}\" begin_offset=\"#{span.offset}\" char_length=\"#{span.length}\">",
              span.atts.scan(/\S+?=".+?"/).map { |att| x, y = att.split('=', 2); "    <attribute name=\"#{x}\" value=#{y}/>" },
              "  </string>"
            ]
          else
            "  <string type=\"#{span.tag}\" begin_offset=\"#{span.offset}\" char_length=\"#{span.length}\"/>"
          end
        end.flatten.compact.join("\n")
        s << "\n" if s.length > 0
        s
      end

      def align_step(x, alignment)
        rsd = alignment.rsd
        rsdp = alignment.rsdp
        stack = alignment.stack
        output = alignment.output
        case x
        when /^<\?xml.+\z/
          return
        when /^<\/(\S+)>\z/
          tag = $1
          if stack.size == 0
            raise 'empty stack'
          else
            span = stack.pop
            if tag == span.tag
              span.length = rsdp - span.offset
              output << span
            else
              puts stack.inspect
              puts x
              puts span
              raise StreamError.new "bad tag: #{x}", @fn
            end
          end
        when /^<(\w\S*)((?:\s\S+)*)\s*\/>\z/
          return
        when /^<(\w\S*)((?:\s\S+)*)\s*>\z/
          span = OpenStruct.new
          span.tag = $1
          span.atts = $2
          span.offset = rsdp
          stack << span
        else
          x = Nokogiri::XML.fragment(x).text
          x = @vacuous.segment_with_punkt(x).first
          rsds = rsd[rsdp...rsdp+x.length]
          if x == rsds
            #puts x
            alignment.rsdp += x.length
          else
            #puts ">#{x}"
            #puts "<#{rsds}"
            xp = 0
            while xp < x.length
              if x[xp] == rsd[rsdp] or ( x[xp] =~ /\p{Space}/ and rsd[rsdp] =~ /\p{Space}/ )
                xp += 1
                rsdp += 1
              else
                b1 = x[xp] =~ /\p{Space}/
                b2 = rsd[rsdp] =~ /\p{Space}/
                if b1 and b2
                  xp += 1
                  rsdp +=1
                elsif b1
                  xp += 1
                elsif b2
                  rsdp += 1
                  while rsdp < rsd.length and rsd[rsdp] =~ /\p{Space}/
                    rsdp += 1
                  end
                  if rsdp == rsd.length
                    raise StreamError.new "missing characters", @fn
                  end
                else
                  raise StreamError.new "character mismatch", @fn
                end
              end
            end
            alignment.rsdp = rsdp
          end
        end
      end

    end
  end
end

