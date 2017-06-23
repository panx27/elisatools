require 'spec_helper'
require_relative '../../../../lib/ldc/text/document'
module LDC
end
module LDC::Text

  class Document
  end

    class T
      attr_accessor :total, :tokenization_filename, :whitespace
      def tokenization_parameters
        { patterns: [ [ /\w+/, "word" ] ] }
      end
      def tokens(s)
        beg, total = 0, 0
        s.scan(/\s+|\S+/).map do |x|
          beg = total
          total += x.length
          if x =~ /\S/
            [ x, 'word', beg, x.length ]
          end
        end.compact
      end
    end


  RSpec.describe Document do

    before :each do
      @d = described_class.new
      @d.string = "This is one. \nThis is two."
      @d.docid = 'docid'
      @d.tokenizer = T.new
      # @a = LDC::Morph::Analyzer.new.parse_yaml YAML4
      # @d.analyzer = @a
    end

    after :each do
    end

    describe '#tokenizer=' do

      it "sets @tokenizer" do
        t = T.new
        @d.tokenizer = t
        expect( @d.tokenizer ).to eq t
      end

      it "sets @tokenization_filename" do
        t = T.new
        t.tokenization_filename = 1
        @d.tokenizer = t
        expect( @d.tokenization_filename ).to be 1
      end

    end

    describe '#create_segmentation' do

      it "raises when no segmenter is set" do
        expect { @d.create_segmentation }.to raise_error
      end

      it "identifies sentence boundaries" do
        @d.create_segmentation :simple
        expect(@d.segment_offsets).to eq [ [ 0, 12 ], [ 14, 12 ] ]
      end

    end

    describe '#segment_offsets' do

      it "identifies sentence boundaries" do
        @d.create_segmentation :simple
        expect(@d.segment_offsets).to eq [ [ 0, 12 ], [ 14, 12 ] ]
      end

    end

    describe '#tokenize' do

      it "tokenizes" do
        @d.create_segmentation :simple
        @d.tokenize T.new
        expect(@d.segments.first.token_quads).to eq [
          [ 'This', 'word', 0, 4 ],
          [ 'is', 'word', 5, 2 ],
          [ 'one.', 'word', 8, 4 ]
        ]
      end

    end

    # describe '#match_secondary_stream' do

    #   it "further tokenizes based on a secondary tokenization" do
    #     d = described_class.new
    #     d.string = "tobeor .. nottobe\nthatis .. thequestion"
    #     d.docid = 'docid'
    #     d.tokenizer = T.new
    #     d.create_segmentation :lines
    #     d.tokenize T.new
    #     d.segments.map { |x| x.tokens }.flatten.each { |x| x.type = 'unknown' }
    #     d.segments[0].tokens[1].type = 'punct'
    #     d.segments[1].tokens[1].type = 'punct'
    #     d.match_secondary_stream [ " to be or . . not to be ", " that is .. the question " ], T.new
    #     expect(d.segments.first.token_quads).to eq [
    #       [ 'to', 'word', 0, 2 ],
    #       [ 'be', 'word', 2, 2 ],
    #       [ 'or', 'word', 4, 2 ],
    #       [ '..', 'punct', 7, 2 ],
    #       [ 'not', 'word', 10, 3 ],
    #       [ 'to', 'word', 13, 2 ],
    #       [ 'be', 'word', 15, 2 ]
    #     ]
    #     expect(d.segments.last.token_quads).to eq [
    #       [ 'that', 'word', 18, 4 ],
    #       [ 'is', 'word', 22, 2 ],
    #       [ '..', 'punct', 25, 2 ],
    #       [ 'the', 'word', 28, 3 ],
    #       [ 'question', 'word', 31, 8 ]
    #     ]
    #   end

    # end

      # describe '#correct' do

      #   it "changes the analysis" do
      #     @d.string = 'things'
      #     @s = LDC::Text::Segment.new(@d, 0, 8)
      #     @d.segments = [ @s ]
      #     @d.tokenize_segment_by_index -1
      #     @d.analyze_segment_by_index -1

      #     new_analysis = LDC::Morph::Analysis.new( 'things', [ 'noun', 'plural' ], nil )
      #     new_analysis.morphemes[0].token = 'thing'
      #     new_analysis.morphemes[1].token = 's'
      #     @s.correct 0, new_analysis #'thing=noun s=plural'
      #     expect(@d.segments.last.token_quads).to eq [
      #       [ 'things', 'word', 0, 6 ]
      #     ]
      #     expect(@s.tokens.first.analysis.to_s).to eq 'thing=noun s=plural'
      #   end

      # end

      # describe '#skip' do

      #   it "changes the analysis to skip a token" do
      #     @s.docs << []
      #     @s.add_tokenize_analyze 'things'
      #     # @s.find_one_analysis_for_words(%w[ things ], @graph)
      #     @s.skip 0
      #     obj = [
      #       { token: 'things', type: 'skip' }
      #     ]
      #     @s.remove_analysis_sets
      #     expect(@s.docs[-1][-1][:tokens].to_yaml).to eq obj.to_yaml
      #   end

      # end



      # describe '#add_segment' do

      #   it "adds original_text" do
      #     # @s.analyze(%w[ one test ]) { |set| set }
      #     # @s.docs << []
      #     @d.add_segment 'one test'
      #     # @s.find_one_analysis_for_words(%w[ one test ], @graph)
      #     expect(@d.segments.first.string).to eq "one test"
      #   end

      #   it "creates empty token array" do
      #     # @s.analyze(%w[ one test ]) { |set| set }
      #     # @s.docs << []
      #     @d.add_segment 'one test'
      #     # @s.find_one_analysis_for_words(%w[ one test ], @graph)
      #     expect(@d.segements.first.tokens).to eq []
      #   end

      # end

      # describe '#add_sentence' do

      #   it "adds original_text" do
      #     # @s.analyze(%w[ one test ]) { |set| set }
      #     # @s.docs << []
      #     @d.add_sentence 'one test'
      #     # @s.find_one_analysis_for_words(%w[ one test ], @graph)
      #     expect(@d.segments.first.string).to eq "one test"
      #   end

      #   it "creates empty token array" do
      #     # @s.analyze(%w[ one test ]) { |set| set }
      #     # @s.docs << []
      #     @d.add_sentence 'one test'
      #     # @s.find_one_analysis_for_words(%w[ one test ], @graph)
      #     expect(@d.segments.first.tokens).to eq []
      #   end

      # end

      # describe '#tokenize_segment' do

      #   it "tokenizes" do
      #     # @s.analyze(%w[ one test ]) { |set| set }
      #     @s.docs << []
      #     @s.add_sentence 'one test'
      #     @s.tokenize_segment @s.docs[-1][-1]
      #     # @s.find_one_analysis_for_words(%w[ one test ], @graph)
      #     expect(@s.docs[-1][-1][:tokens]).to eq [
      #       { token: 'one', type: 'word' },
      #       { token: 'test', type: 'word' }
      #     ]
      #   end

      # end

      describe '#tokenize_segment_by_indices' do

        it "tokenizes" do
          # @s.analyze(%w[ one test ]) { |set| set }
          @d.string = 'one test'
          @d.segments = [ LDC::Text::Segment.new(@d, 0, 8, 'one test') ]
          @d.tokenize_segment_by_index -1
          # @s.find_one_analysis_for_words(%w[ one test ], @graph)
          expect(@d.segments.last.token_quads).to eq [
            [ 'one', 'word', 0, 3 ],
            [ 'test', 'word', 4, 4 ]
          ]
        end

      end

      # describe '#analyze_segment' do

      #   it "analyzes" do
      #     # @s.analyze(%w[ one test ]) { |set| set }
      #     @s.docs << []
      #     @s.add_sentence 'one test'
      #     @s.tokenize_segment @s.docs[-1][-1]
      #     @s.analyze_segment @s.docs[-1][-1]
      #     # @s.find_one_analysis_for_words(%w[ one test ], @graph)
      #     @s.remove_analysis_sets
      #     expect(@s.docs[-1][-1][:tokens]).to eq [
      #       { token: 'one', type: 'word', count: 0 },
      #       { token: 'test', type: 'word', analysis: 'test=noun' }
      #     ]
      #   end

      # end
=begin
      describe '#analyze_tokens' do

        it "analyzes tokens" do
          # @s.analyze(%w[ one test ]) { |set| set }
          @d.string = 'one test'
          @d.segments = [ LDC::Text::Segment.new(@d, 0, 8) ]
          @d.tokenize_segment_by_index -1
          @d.analyze_tokens @d.segments.last.tokens
          # @s.find_one_analysis_for_words(%w[ one test ], @graph)
          # @s.remove_analysis_sets
          expect(@d.segments.last.token_quads).to eq [
            [ 'one', 'word', 0, 3 ],
            [ 'test', 'word', 4, 4 ]
          ]
          one, test = @d.segments.first.tokens.map { |x| x.analysis_set }
          expect(one.count).to be 0
          expect(test.count).to be 1
          a = test.select_valid_analyses[0]
          expect(test.to_lemmatized_string a).to eq "test=test:noun"
        end

      end
=end
      # describe '#reanalyze_token' do

      #   it "reanalyzes" do
      #     # @s.analyze(%w[ one test ]) { |set| set }
      #     @s.docs << []
      #     @s.add_sentence 'one test'
      #     @s.tokenize_segment @s.docs[-1][-1]
      #     @s.analyze_segment @s.docs[-1][-1]
      #     @graph.graph['morphemes']['noun']['one'] = {}
      #     @s.reanalyze_token @s.docs[-1][-1][:tokens][0]
      #     # @s.find_one_analysis_for_words(%w[ one test ], @graph)
      #     @s.remove_analysis_sets
      #     expect(@s.docs[-1][-1][:tokens]).to eq [
      #       { token: 'one', type: 'word', analysis: 'one=noun' },
      #       { token: 'test', type: 'word', analysis: 'test=noun' }
      #     ]
      #   end

      # end
=begin
      describe '#analyze_segment_by_indices' do

        it "analyzes" do
          # @s.analyze(%w[ one test ]) { |set| set }
          @d.string = 'one test'
          @d.segments = [ LDC::Text::Segment.new(@d, 0, 8) ]
          @d.tokenizer = Tokenizer.new
          @d.tokenize_segment_by_index -1
          @d.analyze_segment_by_index -1

          # @s.find_one_analysis_for_words(%w[ one test ], @graph)
          # @d.remove_analysis_sets
          expect(@d.segments.last.token_quads).to eq [
            [ 'one', 'word', 0, 3 ], #count: 0 },
            [ 'test', 'word', 4, 4 ] # analysis: 'test=noun' }
          ]
          one, test = @d.segments.first.tokens.map { |x| x.analysis_set }
          expect(one.count).to be 0
          expect(test.count).to be 1
          a = test.select_valid_analyses[0]
          expect(test.to_lemmatized_string a).to eq "test=test:noun"
        end

      end
=end
  end

end
