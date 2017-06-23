require 'spec_helper'
require_relative '../../../../lib/ldc/text/tokenizer'

module LDC
  module Text

    RSpec.describe Tokenizer do

      before :each do
        @t = described_class.new
      end

      describe "#token_count" do

        it "calls #tokens then calls #count on the result" do
          allow(@t).to receive(:tokens).and_return [ 1, 2, 3 ]
          expect(@t.token_count '').to be 3
        end

      end

      describe "#tokens" do

        it "raises if the parameters haven't been set" do
          expect { @t.tokens '' }.to raise_error "tokenization parameters haven't been set"
        end

        it "parses xml and handles languages according to 'lang' attribute" do
          @t.tokenization_parameters = { preprocessor: :xml }
          s = '<doc><div lang="cmn">现在中国的形势是</div> <div lang="eng">hello world</div></doc>'
          expect(@t.tokens(s)).to eq %w[ 现 在 中 国 的 形 势 是 hello world ]
        end

        it "separates punctuation" do
          @t.tokenization_parameters = { tokenizer: :punctuation }
          s = "To be or not-to be?"
          expect(@t.tokens(s).map(&:first)).to eq %w[ To be or not - to be ? ]
        end

        it "doesn't separate sequences of punctuation" do
          @t.tokenization_parameters = { tokenizer: :punctuation }
          s = "To be or not--to be??"
          expect(@t.tokens(s).map(&:first)).to eq %w[ To be or not -- to be ?? ]
        end

        it "uses patterns" do
          @t.tokenization_parameters = {
              tokenizer: :patterns,
              patterns: [
                [ /^(\w+)\z/, 'word' ],
                [ /^(\w+)(-to)\z/, 'word x' ],
                [ /(e\?)/, 'y' ]
              ]
            }
          s = "To be or not-to be?"
          expect(@t.tokens s).to eq [
            [ 'To', 'word', 0, 2 ],
            [ 'be', 'word', 3, 2 ],
            [ 'or', 'word', 6, 2 ],
            [ 'not', 'word', 9, 3 ],
            [ '-to', 'x', 12, 3 ],
            [ 'e?' , 'y', 17, 2 ]
          ]

        end

      end

      describe '#calculate_offsets_from_complete_tokenization' do

        it "returns quads given the original string and the tokens" do
          s = "To be or not-to be?"
          tokens = %w[ To be or not -to b e? ]
          expect(@t.calculate_offsets_from_complete_tokenization(s,tokens)).to eq [
            [ 'To', 'unknown', 0, 2 ],
            [ 'be', 'unknown', 3, 2 ],
            [ 'or', 'unknown', 6, 2 ],
            [ 'not', 'unknown', 9, 3 ],
            [ '-to', 'unknown', 12, 3 ],
            [ 'b', 'unknown', 16, 1 ],
            [ 'e?' , 'unknown', 17, 2 ]
          ]
        end          

      end




      describe '#tokenize_by_language' do

        it "calls #tokenize_by_words for :eng" do
          s = ''
          allow(@t).to receive(:tokenize_by_words).and_return true
          expect(@t.tokenize_by_language(s, :eng)).to be true
        end

        it "calls #tokenize_by_characters for :cmn" do
          s = ''
          allow(@t).to receive(:tokenize_by_characters).and_return true
          expect(@t.tokenize_by_language(s, :cmn)).to be true
        end

        it "raises for an unknown language" do
          s = ''
          expect { @t.tokenize_by_language(s, :x) }.to raise_error(/unknown/)
        end

      end

      describe '#tokenize' do

        it "returns token, type, offset, and length for each token" do
          s = "To be or not-to be?"
          @t.tokenization_parameters = {
            tokenizer: :patterns,
            patterns: [
              [ /e\?/, nil ],
              [ /^(\w+)(-to)\z/, nil ],
              [ /\w+/, nil ],
            ]
          }
          expect(@t.tokenize s).to eq [
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
          @t.tokenization_parameters = {
            tokenizer: :patterns,
            patterns: [
              [ /^\w+/, nil ],
              [ /^(\w+)(-to)\z/, nil ],
              [ /e\?/, nil ]
            ]
          }
          expect(@t.tokenize s).to eq [
            [ 'To', nil, 0, 2 ],
            [ 'be', nil, 3, 2 ],
            [ 'or', nil, 6, 2 ],
            [ 'not', nil, 9, 3 ],
            [ 'be', nil, 16, 2 ]
          ]
        end

        it "returns the types if given" do
          s = "To be or not-to be?"
          @t.tokenization_parameters = {
            tokenizer: :patterns,
            patterns: [
              [ /^(\w+)\z/, 'word' ],
              [ /^(\w+)(-to)\z/, 'word x' ],
              [ /(e\?)/, 'y' ]
            ]
          }
          expect(@t.tokenize s).to eq [
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
          @t.tokenization_parameters = {
            tokenizer: :patterns,
            patterns: [
              [ /^(\w+)\z/, 'word' ],
              [ /^(\w+)(-to)\z/, 'word x x' ],
              [ /(e\?)/, 'y' ]
            ]
          }
          expect { @t.tokenize s }.to raise_error
        end

        it "won't capture whitespace" do
          s = "To be or not-to be?"
          @t.tokenization_parameters = {
            tokenizer: :patterns,
            patterns: [
              [ /^(\w+)\z/, 'word' ],
              [ /.+/, 'other' ]
            ]
          }
          expect(@t.tokenize s).to eq [
            [ 'To', 'word', 0, 2 ],
            [ 'be', 'word', 3, 2 ],
            [ 'or', 'word', 6, 2 ],
            [ 'not-to', 'other', 9, 6 ],
            [ 'be?' , 'other', 16, 3 ]
          ]
        end

        it "matches recursively" do
          s = "To be or not-to be?"
          @t.tokenization_parameters = {
            tokenizer: :patterns,
            recursive_types: %w[ r ],
            patterns: [
              [ /^(.+)(-)(.+)\z/, 'r other r' ],
              [ /^(.+)(\?)\z/, 'r other' ],
              [ /^(\w+)\z/, 'word' ],
              [ /.+/, 'other' ]
            ]
          }
          expect(@t.tokenize s).to eq [
            [ 'To', 'word', 0, 2 ],
            [ 'be', 'word', 3, 2 ],
            [ 'or', 'word', 6, 2 ],
            [ 'not', 'word', 9, 3 ],
            [ '-', 'other', 12, 1 ],
            [ 'to', 'word', 13, 2 ],
            [ 'be', 'word', 16, 2 ],
            [ '?', 'other', 18, 1 ]
          ]
        end

      end      

      describe '#tokenize_by_language' do

        it 'handles normal English sentences' do
          s = "To be or not to be?"
          expect(@t.tokenize_by_language(s, :eng)).to eq %w[ To be or not to be ]
        end

        it 'accepts some other language codes for word parsing' do
          s = "To be or not to be?"
          allow(@t).to receive(:tokenize_by_words).and_return true
          expect(@t.tokenize_by_language(s, :arb)).to be true
          expect(@t.tokenize_by_language(s, :arz)).to be true
          expect(@t.tokenize_by_language(s, 'English')).to be true
          expect(@t.tokenize_by_language(s, 'Arabic')).to be true
          expect(@t.tokenize_by_language(s, 'French')).to be true
        end

        it "handles Chinese with punctuation" do
          s = "现在中国的形势是：银行行长"
          expect(@t.tokenize_by_language(s, :cmn)).to eq %w[ 现 在 中 国 的 形 势 是 银 行 行 长 ]
        end

        it 'accepts some other language codes for character parsing' do
          s = "To be or not to be?"
          allow(@t).to receive(:tokenize_by_characters).and_return true
          expect(@t.tokenize_by_language(s, 'Chinese')).to be true
          expect(@t.tokenize_by_language(s, 'Mandarin')).to be true
        end

        it "raises for an unknown language" do
          s = ''
          expect { @t.tokenize_by_language(s, :x) }.to raise_error(/unknown/)
        end

      end

    end

  end
end

