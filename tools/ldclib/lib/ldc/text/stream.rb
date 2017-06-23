require_relative 'ltf'
require_relative 'tokenizer'
require_relative 'document'
require 'diffy'
require 'sequel'
require 'sqlite3'
require 'ostruct'
module LDC
  module Text

    # should be raised low enough to associate with a specific input
    class StreamError < StandardError

      attr_accessor :i

      def initialize(m, i)
        @i = i
        super m
      end

    end

    class Stream

      attr_accessor :same_io, :document, :segment_index, :files
      attr_reader :analyzer

      def initialize(tokenizer: nil, analyzer: nil, diff: nil, tokenizer2: nil, operator: nil, secondary: nil, x: false)
        if tokenizer2
          @stream2 = Stream.new(tokenizer: tokenizer2)
        end
        self.tokenizer = tokenizer if tokenizer
        self.analyzer = analyzer if analyzer
        @diff = diff
        @ltf = LDC::Text::LTF.new
        @operator = operator
        if secondary
          @secondary = File.readlines(secondary)
          unless x
            @original_tokenizer = @tokenizer
            @tokenizer = LDC::Text::Tokenizer.new
            @tokenizer.tokenization_parameters = { tokenizer: :patterns, patterns: [ [ /^.+\z/, 'unknown' ] ] }
          end
        end
      end

      # def main(x)
      #   raise 'called #main from superclass'
      #   # # check_rsd xml
      #   # # x = @ltf.ltf2rsd xml
      #   # puts count_tokens doc
      # end

      # def check_rsd(xml)
      #   x = @ltf.ltf2rsd xml
      #   rsd = ltf.sub('ltf','rsd').sub('.ltf.xml','.rsd.txt')
      #   y = `unzip -p #{fn.sub 'ltf', 'rsd'} #{rsd}`
      #   puts ltf unless x == y
      # end
      # 
#case ARGV[0]
#when 'ltf', 'rsd', 'docs', 'tokens'

      def get_zip_files
        x = @corpus_spec['path']
        y = @corpus_spec['data'].first['paths'].first
        Dir["#{x}/#{y}/*.ltf.zip"]
      end

      def unit
      end

      def zip_helper(fn, del, type)
        open("|unzip -p #{fn}") do |p|
          p.each(del) do |s|
            @i += 1
            # puts i if i % 10000 == 0
            break if @i == @limit
            run_over_type_helper2(type, s) { |x| main x }
          end
        end
      end

      def run_over_type(zip_files:, limit: nil)
        type = unit
        @i = -1
        @limit = limit
        zip_files.each do |fn, ofile|
          case fn
          when /\.ltf\.zip\z/
            next if type =~ /doc/i
            del = type == 'tweets' ? "\n" : "</LCTL_TEXT>\n"
            zip_helper fn, del, type
          when /\.xml\.zip\z/
            next unless type =~ /doc/i
            zip_helper fn, "</#{type}>\n", type
          else
            next unless type =~ /doc/i
            del = "</DOC>\n" if type == 'DOC'
            del = "</doc>\n" if type == 'doc'
            @i += 1
            # puts i if i % 10000 == 0
            break if @i == @limit
            run_over_type_helper2(type, File.read(fn)) { |x| main x }
          end
          break if @i == @limit
        end
        done
      end

      def main(x)
        puts x
      end

      def doc(x)
        main x
      end

      def done
      end

      def run_over_type_helper2(type, s)
        case type
        when 'segments'
          run_over_type_helper('docs', s).segments.each { |x| yield x }
        when 'tokens'
          run_over_type_helper('docs', s).segments.map { |x| x.tokens }.flatten.each { |x| yield x }
        else
          yield run_over_type_helper(type, s)
        end
      end

      def run_over_type_helper(type, s)
        case type
        when 'ltf'
          s
        when 'rsd'
          @ltf.ltf2rsd s
        when 'docs'
          create_doc2 s
        when 'tweets'
          s
        when 'doc', 'DOC'
          doc s
        else
          #raise "bad type: #{type}"
          main s
        end
      end

      def run_over_io_pairs(paired_io_filenames)
        @pointer = OpenStruct.new
        @paired_io_filenames = paired_io_filenames
        @paired_io_filenames.map.with_index do |io, ii|
          @paired_io_index = ii
          run_io *io
        end
      end

      def run_io(i, o)
        if @tokenizer
          tokenize i, o
        else
          raise "don't know what to run"
        end
      end

      def tokenize(i, o)
        input_string = File.read i
        # output_string = yield i, o, input_string
        output_string = helper1 i, o, input_string

        if @diff == :ltf
          # diff the created LTF with the existing one
          raise "can't diff LTF because the output file doesn't exist" unless File.exists? o
          Diffy::Diff.new(File.read(o), output_string, context: 1).to_s
        elsif @stream2
          Diffy::Diff.new( tokens_for_diff(input_string), @stream2.tokens_for_diff(input_string) , context: 1 )
        elsif @analyzer
          output_string
        elsif o
          open(o, 'w') { |f| f.puts output_string }
          nil
        else
          output_string
        end
      end

      def helper1(input_fn, output_fn, input_string)
        if @tokenizer == :untokenize
          ltf2rsd input_string
        else
          if @tokenizer
            doc = rsd2doc input_fn, input_string
            if @analyzer
              analyze doc
            end
            doc2ltf doc
          elsif @analyzer
            #output_string = stream.fast_analysis output_fn
            # output_string = stream.analyze_input_string input_string
            raise "can't analyze"
          else
            raise "neither tokenizer nor grammar given"
          end
          # next if $options.save_cache
        end
      end

      def tokens_for_diff(string)
        rsd2doc('blank.rsd.txt', string).segments.map { |x| x.token_quads.map { |x| "#{x[1]} #{x[0]}" } }.flatten.join "\n"
      end

      def tokenizer=(fn)
        if fn == :untokenize
          @tokenizer = fn
        else
          if fn.kind_of? LDC::Text::Tokenizer
            @tokenizer = fn
          else
            @tokenizer = LDC::Text::Tokenizer.new
            @tokenizer.init_from_yaml_file fn
          end
        end
      end

      def analyzer=(fn)
        @analyzer = LDC::Morph::Analyzer.new fn: fn
        # analyzer.load_cache_from_yaml_file "#{fn}.cache" if $options.read_cache
      end

      def ltf2rsd(string)
        @ltf ||= LDC::Text::LTF.new
        @ltf.ltf2rsd string
      end

      def rsd2doc(input, string)
        # create doc
        doc = LDC::Text::Document.new
        doc.string = string
        doc.docid = File.basename input, '.rsd.txt'
        doc.tokenizer = @tokenizer
        doc.create_segmentation :lines
        doc.tokenize_all_segments
        # doc.match_secondary_stream @secondary.shift(doc.segments.length), @original_tokenizer if @secondary
        doc
      end

      def analyze(doc)
        doc.analyzer = @analyzer
        doc.analyze_all_segments_accept_and_simplify_first_valid_analysis
      end

      def doc2ltf(doc)
        @ltf ||= LDC::Text::LTF.new
        @ltf.doc2xml doc
      end

      def fast_analysis(output)
        @ltf ||= LDC::Text::LTF.new
        # STDERR.puts "#{Time.now} pair #{i}" if i % 1000 == 0
        file = File.read output
        cache = @analyzer.analyze2 @ltf.unique_word_token_strings file
        @ltf.fast_analysis file, cache, @analyzer.grammar_filename
      end

      def find_first_segment_index_without_tokens(i)
        doc = @document
        i = validate_segment_index i
        while i and doc.segments[i] and doc.segments[i].tokens.size > 0
          i += 1
        end
        i
      end

      def find_first_segment_index_with_untagged_token(i)
        doc = @document
        i = validate_segment_index i
        while i and doc.segments[i]
          break if doc.segments[i].tokens.any? { |x| x.analysis.nil? }
          i += 1
        end
        i
      end

      # main will get called on first untokenized segment
      def skip_tokenized_segments
        @segment_index = find_first_segment_index_without_tokens 0
      end

      # main will get called on first segment with at least one untagged token
      def skip_tagged_tokens
        @segment_index = find_first_segment_index_with_untagged_token 0
      end

      # see specs
      def validate_segment_index(i)
        doc = @document
        (i.class == Fixnum and i >= 0 and i < doc.segments.count) ? i : false
      end

      # checks indices from terminal, which are strings and 1 based
      def check_human_token_index(i)
        doc = @document
        if i =~ /^\d+\z/ and i.to_i > 0 and i.to_i < doc.segments[@segment_index].tokens.count + 1
          i.to_i
        else
          false
        end
      end

      def setup
        @paired_io_index = 0
        output = @paired_io_filenames.first.first
        doc = create_doc output
        @ltf.parse_xml doc, File.read(output)
        @document = doc
      end

      # sets up a Document object
      def create_doc(fn)
        doc = LDC::Text::Document.new
        doc.docid = File.basename(fn, '.rsd.txt')
        doc.string = File.read fn
        # doc.tokenizer = @tokenizer
        doc.analyzer = @analyzer
        doc
      end

      def create_doc2(xml)
        doc = LDC::Text::Document.new
        @ltf.parse_xml doc, xml
        doc
      end

      def goto_segment_index(i)
        @segment_index = validate_segment_index i
      end

      def goto_next_segment
        goto_segment_index @segment_index + 1
      end

      # previously used by auto shell
      def analyze_for_shell
        i = @segment_index
        @document.tokenize_segment_by_index i
        @document.analyze_segment_by_index i
        @document.segments[i].accept_and_simplify_first_valid unless $options.none
      end

      def segment_for_shell(x)
        @document.create_segmentation( x == :gw ? :gw : :lines )
      end

      def current_segment
        @document.segments[@segment_index]
      end

      def analyze_current_segment
        # doc.tokenize_segment_by_index i
        @document.analyze_segment_by_index @segment_index
      end

      def save_ltf
        output = @paired_io_filenames[@paired_io_index][1]
        open(output, 'w') do |f|
          s = @ltf.doc2xml @document
          f.puts s
        end
        if $log.size > 0
          open("#{output}.log", 'a') do |f|
            f.puts $log
          end
        end
      end

    end
  end
end

