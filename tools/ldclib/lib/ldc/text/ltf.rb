require 'nokogiri'
require 'digest/md5'
module LDC
  module Text
    class LTF

      def unique_word_token_strings(file)
        file.scan(/<TOKEN.+?pos=\"(?:word|[A-Z]+)\".+?>(.+?)</).flatten.uniq
      end

      def fast_analysis(file, cache, analyzer_grammar_filename)
        file.sub!( /grammar\S+/, "grammar=\"#{analyzer_grammar_filename}\">" )
        file.gsub!(/(<TOKEN.+?pos=\")(\w+)(.+?morph=\").*?(\".+?>(.+?)<)/) do
          x, pos, y, z, string = $1, $2, $3, $4, $5
          a = cache[string]
          analysis = pos =~ /^(word|[A-Z]+)\z/ ? (a.size > 0 ? a.first.last : 'none') : 'none'
          case pos
          when /^(word|[A-Z]+)\z/
            p = a.size > 0 ? a.first.first : 'X'
          when /num/
            p = 'NUM'
          when 'punct'
            p = '.'
          else
            p = pos
          end
          "#{x}#{p}#{y}#{analysis}#{z}"
        end
      end

      def doc2xml(doc)
        grammar = doc.grammar_filename
        grammar = 'none' if grammar.nil? or grammar == ''
        tokenization = doc.tokenization_filename
        tokenization = 'none' if tokenization.nil? or tokenization == ''
        text_attributes = if $options and $options.suppress_text_attributes
          ''
        else
          " raw_text_char_length=\"#{doc.string.length}\" raw_text_md5=\"#{Digest::MD5.hexdigest(doc.string)}\""
        end
        ([
          "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE LCTL_TEXT SYSTEM \"ltf.v1.5.dtd\">\n<LCTL_TEXT>\n",
          "<DOC id=\"#{doc.docid}\" tokenization=\"#{tokenization}\" grammar=\"#{grammar}\"#{text_attributes}>\n",
          "<TEXT>\n"
        ] +
        doc.segments.map.with_index do |seg, i|
          [
            "<SEG id=\"segment-#{i}\" start_char=\"#{seg.offset}\" end_char=\"#{seg.end}\">\n",
            "<ORIGINAL_TEXT>#{seg.string.encode(xml: :text)}</ORIGINAL_TEXT>\n"
          ] +
          seg.tokens.map.with_index do |token, j|
            analysis = token.analysis || 'none'
            "<TOKEN id=\"token-#{i}-#{j}\" pos=\"#{token.type}\" morph=\"#{analysis.encode(xml: :text)}\" start_char=\"#{token.offset}\" end_char=\"#{token.end}\">#{token.string.encode(xml: :text)}</TOKEN>\n"
          end +
          [ "</SEG>\n" ]
        end +
        [ "</TEXT>\n</DOC>\n</LCTL_TEXT>\n" ]).flatten.join
      end

      def parse_xml(document, xml)
        document.segments = []
        Nokogiri::XML(xml).css('DOC').each do |doc|
          doc.css('SEG').each do |seg|
            a, b = seg[:start_char].to_i, seg[:end_char].to_i
            check = seg.css('ORIGINAL_TEXT').first.text
            document.segments << Segment.new( document, a, b - a + 1, check )
            raise "bad input" unless check == document.segments[-1].string
            seg.css('TOKEN').each do |token|
              a, b = token[:start_char].to_i, token[:end_char].to_i
              t = Token.new document: document, type: token[:pos], offset: a, token: token.text
              document.segments[-1].tokens << t
              case token[:morph]
              when 'none'
                t.analysis = nil
              else
                t.analysis = token[:morph]
                # if defined? LDC::Morph::Analysis
                #   raise 'need an analyzer for the analyses' unless @analyzer
                #   t.analysis_set = LDC::Morph::AnalysisSet.new token.text
                #   t.analysis_set.graph = @analyzer.graph
                #   t.analysis = t.analysis_set.analysis_from_string token[:morph]
                # end  
              end
            end
          end
        end
      end

      def ltf2rsd(ltf)
        rsd = ''
        xml = Nokogiri::XML ltf
        offset = 0
        xml.css('SEG').each do |seg|
          b = seg['start_char'].to_i
          diff = b - offset
          rsd << "\n" * diff
          offset += diff + ( seg['end_char'].to_i - b + 1 )
          rsd << seg.css('ORIGINAL_TEXT').first.text
        end
        doc = xml.css('DOC').first
        length = doc['raw_text_char_length']
        diff = length ? length.to_i - rsd.length : 2
        rsd << "\n" * diff
        md5 = doc['raw_text_md5']
        raise "doc #{doc['id']} doesn't match its checksum" if md5 and Digest::MD5.hexdigest(rsd) != md5
        rsd
      end

    end
  end
end
