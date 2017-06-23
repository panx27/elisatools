require 'spec_helper'

module LDC
  module Text

    RSpec.describe TokenizerPunct do

      before :each do
        @t = described_class.new
      end

      describe '#tokenize' do

        it "includes punctuation in token stream" do
          s = "To be or not-to be?"
          expect(@t.tokenize(s).map(&:first)).to eq %w[ To be or not - to be ? ]
        end

      end

    end

  end
end

