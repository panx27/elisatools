require 'spec_helper'

module LDC
  module Text

    RSpec.describe 'TokenizationStringMixin' do

      before :each do
        @t = Tokenizer.new
        String.tokenizer = @t
      end

      describe '#tokenize_by_words' do

        it 'handles normal English sentences' do
          s = "To be or not to be?"
          expect(s.tokenize_by_words).to eq %w[ To be or not to be ]
        end

        it "punctuation creates separate words" do
          s = "some-thing"
          expect(s.tokenize_by_words).to eq %w[ some thing ]
        end

      end

      describe '#tokenize_by_characters' do

        it "handles Chinese with punctuation" do
          s = "现在中国的形势是：银行行长"
          expect(s.tokenize_by_characters).to eq %w[ 现 在 中 国 的 形 势 是 银 行 行 长 ]
        end

      end

      describe '#tokenize_by_punctuation' do

        it "includes punctuation in token stream" do
          s = "To be or not-to be?"
          expect(s.tokenize_by_punctuation).to eq %w[ To be or not - to be ? ]
        end

      end

      describe '#tokenize_by_language' do

        it "calls #tokenize_by_words for :eng" do
          s = ''
          allow(@t).to receive(:tokenize_by_words).and_return true
          expect(s.tokenize_by_language(:eng)).to be true
        end

        it "calls #tokenize_by_characters for :cmn" do
          s = ''
          allow(@t).to receive(:tokenize_by_characters).and_return true
          expect(s.tokenize_by_language(:cmn)).to be true
        end

        it "raises for an unknown language" do
          s = ''
          expect { s.tokenize_by_language(:x) }.to raise_error(/unknown/)
        end

      end

      describe '#tokenize_by_patterns' do

        it "returns token, type, offset, and length for each token" do
          s = "To be or not-to be?"
          patterns = [
            [ /e\?/, nil ],
            [ /^(\w+)(-to)\z/, nil ],
            [ /\w+/, nil ],
          ]
          expect(s.tokenize_by_patterns(patterns)).to eq [
            [ 'To', nil, 0, 2 ],
            [ 'be', nil, 3, 2 ],
            [ 'or', nil, 6, 2 ],
            [ 'not', nil, 9, 3 ],
            [ '-to', nil, 12, 3 ],
            [ 'e?' , nil, 17, 2 ]
          ]
        end

        it "uses patterns in order" do
          s = "To be or not-to be?"
          # the first pattern prevents the application of the other two
          patterns = [
            [ /^\w+/, nil ],
            [ /^(\w+)(-to)\z/, nil ],
            [ /e\?/, nil ]
          ]
          expect(s.tokenize_by_patterns(patterns)).to eq [
            [ 'To', nil, 0, 2 ],
            [ 'be', nil, 3, 2 ],
            [ 'or', nil, 6, 2 ],
            [ 'not', nil, 9, 3 ],
            [ 'be', nil, 16, 2 ]
          ]
        end

        it "returns the types if given" do
          s = "To be or not-to be?"
          patterns = [
            [ /^(\w+)\z/, 'word' ],
            [ /^(\w+)(-to)\z/, 'word x' ],
            [ /(e\?)/, 'y' ]
          ]
          expect(s.tokenize_by_patterns(patterns)).to eq [
            [ 'To', 'word', 0, 2 ],
            [ 'be', 'word', 3, 2 ],
            [ 'or', 'word', 6, 2 ],
            [ 'not', 'word', 9, 3 ],
            [ '-to', 'x', 12, 3 ],
            [ 'e?' , 'y', 17, 2 ]
          ]
        end

        it "raises on length mismatch for types and captures" do
          s = "To be or not-to be?"
          patterns = [
            [ /^(\w+)\z/, 'word' ],
            [ /^(\w+)(-to)\z/, 'word x x' ],
            [ /(e\?)/, 'y' ]
          ]
          expect { s.tokenize_by_patterns(patterns) }.to raise_error
        end

        it "won't capture whitespace" do
          s = "To be or not-to be?"
          patterns = [
            [ /^(\w+)\z/, 'word' ],
            [ /.+/, 'other' ]
          ]
          expect(s.tokenize_by_patterns(patterns)).to eq [
            [ 'To', 'word', 0, 2 ],
            [ 'be', 'word', 3, 2 ],
            [ 'or', 'word', 6, 2 ],
            [ 'not-to', 'other', 9, 6 ],
            [ 'be?' , 'other', 16, 3 ]
          ]
        end

      end      

      describe '#tokenize_by_language' do

        it 'handles normal English sentences' do
          s = "To be or not to be?"
          expect(s.tokenize_by_language(:eng)).to eq %w[ To be or not to be ]
        end

        it 'accepts some other language codes for word parsing' do
          s = "To be or not to be?"
          allow(@t).to receive(:tokenize_by_words).and_return true
          expect(s.tokenize_by_language(:arb)).to be true
          expect(s.tokenize_by_language(:arz)).to be true
          expect(s.tokenize_by_language('English')).to be true
          expect(s.tokenize_by_language('Arabic')).to be true
          expect(s.tokenize_by_language('French')).to be true
        end

        it "handles Chinese with punctuation" do
          s = "现在中国的形势是：银行行长"
          expect(s.tokenize_by_language(:cmn)).to eq %w[ 现 在 中 国 的 形 势 是 银 行 行 长 ]
        end

        it 'accepts some other language codes for character parsing' do
          s = "To be or not to be?"
          allow(@t).to receive(:tokenize_by_characters).and_return true
          expect(s.tokenize_by_language('Chinese')).to be true
          expect(s.tokenize_by_language('Mandarin')).to be true
        end

        it "raises for an unknown language" do
          s = ''
          expect { s.tokenize_by_language(:x) }.to raise_error(/unknown/)
        end

      end

    end
    
  end
end

