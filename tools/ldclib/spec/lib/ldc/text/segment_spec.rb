require 'spec_helper'
require_relative '../../../../lib/ldc/text/segmenter'
module LDC::Text
    class T
      attr_accessor :total, :whitespace
      def tokens(s)
        beg, total = 0, 0
        s.scan(/\s+|\S+/).map do |x|
          beg = total
          total += x.length
          if x =~ /\S/
            [ x, 'word', beg, x.length ]
            # x
          end
        end.compact
      end
    end

  RSpec.describe Segment do

    before :each do
      @d = Document.new
      @d.string = "This is one. \nThis is two."
      @d.create_segmentation :simple
      @s = @d.segments.first
    end

    after :each do
    end

    describe '#string' do

      it "gets the string for the segment" do
        expect(@s.string).to eq 'This is one.'
      end

    end

    describe '#tokenize' do

      it "tokenizes" do
        @s.tokenize T.new
        expect(@s.token_quads).to eq [
          [ 'This', 'word', 0, 4 ],
          [ 'is', 'word', 5, 2 ],
          [ 'one.', 'word', 8, 4 ]
        ]
      end

    end

    # describe '#accept_unique_valid' do

    #   it "sets @analysis if there's a unique valid analysis" do
    #     # @s.analyze(%w[ one test ]) { |set| set }
    #     @d.string = 'one test'
    #     @d.segments = [ LDC::Text::Segment.new(@d, 0, 8) ]
    #     @d.tokenizer = Tokenizer.new
    #     @d.tokenize_segment_by_index -1
    #     @d.analyzer = LDC::Morph::Analyzer.new.parse_yaml YAML4
    #     @d.analyze_segment_by_index -1
    #     @d.segments.first.accept_unique_valid
    #     # @d.analyze_tokens @d.segments.last.tokens
    #     # @s.find_one_analysis_for_words(%w[ one test ], @graph)
    #     # @s.remove_analysis_sets
    #     expect(@d.segments.last.token_quads).to eq [
    #       [ 'one', 'word', 0, 3 ],
    #       [ 'test', 'word', 4, 4 ]
    #     ]
    #     one, test = @d.segments.first.tokens.map { |x| x.analysis_set }
    #     expect(one.count).to be 0
    #     expect(test.count).to be 1
    #     expect(test.analyses.count).to be 1
    #     a = @d.segments.first.tokens.last.analysis
    #     expect(@d.segments.first.tokens.last.analysis_set.analyzer.simplify_and_lemmafy a).to eq "test:tt=nn"
    #   end

    # end

    describe '#include_token?' do

      it "returns true for a token within its bounds" do
        t = Token.new offset: 1, token: ''
        expect(@s.include_token? t).to be true
      end

      it "returns false for a token outside its bounds" do
        t = Token.new offset: 20, token: ''
        expect(@s.include_token? t).to be false
      end

    end

  end

end
