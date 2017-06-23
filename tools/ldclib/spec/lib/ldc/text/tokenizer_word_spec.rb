require 'spec_helper'

module LDC
  module Text

    RSpec.describe TokenizerWord do

      before :each do
        @t = described_class.new
      end

      describe '#tokenize' do

        it 'handles normal English sentences' do
          s = "To be or not to be?"
          expect(@t.tokenize s).to eq [
            [ 'To', 'word', 0, 2 ],
            [ 'be', 'word', 3, 2 ],
            [ 'or', 'word', 6, 2 ],
            [ 'not', 'word', 9, 3 ],
            [ 'to', 'word', 13, 2 ],
            [ 'be', 'word', 16, 2 ]
          ]
        end

        it "punctuation creates separate words" do
          s = "some-thing"
          expect(@t.tokenize(s).map(&:first)).to eq %w[ some thing ]
        end

      end

    end

  end
end