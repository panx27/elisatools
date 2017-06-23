require_relative 'segmenter'
module LDC
  module Text

    class Document

      attr_accessor :string, :segments, :docid, :whitespace
      attr_reader :tokenizer, :tokenization_filename, :analyzer, :grammar_filename

      def tokenizer=(x)
        @tokenization_filename = x.tokenization_filename
        @tokenizer = x
      end

      def analyzer=(x)
        @grammar_filename = x.grammar_filename
        @analyzer = x
      end

      def create_segmentation(type)
        @segments = Segmenter.new(type: type).segment @string
      end

      def segment_offsets
        @segments.map { |x| [ x.offset, x.length ] }
      end

      def tokenize(tokenizer)
        @segments.map { |x| x.tokenize tokenizer }
      end

      def import_preparse(input)
        @segments.each_with_index do |segment, i|
          tokens = Array.new
          while ((line = input.readline.strip) != "") || ((line = input.readline.strip) != "")
            token, type = line.split("\t")
            if token == '-LRB-'
              token = '('
            elsif token == '-RRB-'
              token = ')'
            end
            tokens << {string: token, type: type}
          end
          bad_tokens = Array.new
          segment.tokens.each do |ltf_token|
            j = tokens.find_index { |t| t[:string] == ltf_token.string }
            if j.nil?
              bad_tokens << ltf_token.string
            else
              parsed_token = tokens.delete_at(j)
              if parsed_token[:type] == '.'
                ltf_token.analysis = "none"
              else
                ltf_token.analysis = "#{parsed_token[:string]}=#{parsed_token[:type]}"
              end
            end
          end
          unless bad_tokens.empty?
            unmapped_tokens = tokens.map { |t| t[:string] }.join ' '
            warn "Segment #{i}: unable to match token(s) [#{bad_tokens.join(' ')}] with [#{unmapped_tokens}]"
          end
        end
      end

      def check
        changes = {}
        @segments.each do |seg|
          seg.tokens.each do |token|
            case token.type
            when /punct|number|numstring|unknown|url|html_entity|email|twitter/
              next
            else
              case token.analysis
              when nil
                raise token.string
              when 'unanalyzable'
                next
              else
                # set = @analyzer.analyze_string token.string
                a = token.analysis
                if a =~ /:/
                  next
                else
                  b = @analyzer.simplify token.analysis
                  if a != b
                    changes["#{a}|#{b}"] = false
                  end
                end
              end
            end
          end
        end
        changes
      end

      def change(changes)
        @segments.each do |seg|
          seg.tokens.each do |token|
            case token.type
            when 'punct', 'number', 'unknown'
              next
            else
              case token.analysis
              when nil
                raise token.string
              when 'unanalyzable'
                next
              else
                a = token.analysis
                if a =~ /:/
                  next
                else
                  b = @analyzer.simplify token.analysis
                  if changes["#{a}|#{b}"]
                    token.analysis = b
                    token.type = changes["#{a}|#{b}"]
                  end
                end
              end
            end
          end
        end
      end

      def analyze_segment_by_index(seg)
        analyze_segment @segments[seg]
      end

      def analyze_segment(segment)
        analyze_tokens segment.tokens
      end

      def analyze_tokens(tokens)
        words = tokens.select { |x| x.type =~ /^(word|[A-Z]+)\z/ }
        cache = @analyzer.analyze_strings words.map(&:string).uniq
        words.each do |word|
          word.analysis_set = cache[word.string]
        end
        # @analyzer.analyze(tokens) do |token, set|
        #   if token.type =~ 
        #     token.analysis_set = set
        #     set.parse_token
        #   end
        # end
      end

      def tokenize_segment_by_index(seg)
        tokenize_segment @segments[seg]
      end

      def tokenize_segment(segment)
        segment.tokenize @tokenizer
      end

      def tokenize_all_segments
        count = @segments.count
        @segments.each_with_index do |segment, i|
          # STDERR.puts "#{i} of #{count}"
          segment.tokenize @tokenizer
        end
      end


      def analyze_all_segments_accept_and_simplify_first_valid_analysis
        count = @segments.count
        @segments.each_with_index do |segment, i|
          # STDERR.puts "#{i} of #{count}"
          analyze_segment_by_index i
          segment.accept_and_simplify_first_valid
        end
      end

      def remove_analysis_sets
        @segments.each do |seg|
          seg.tokens.each do |token|
            token.analysis_set = nil
          end
        end
      end

    end

  end
end
