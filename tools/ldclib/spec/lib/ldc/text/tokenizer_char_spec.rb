require 'spec_helper'
require_relative '../../../../lib/ldc/text/tokenizer_char'

module LDC
  module Text

    RSpec.describe TokenizerChar do

      before :each do
        @t = described_class.new
      end
      describe '#tokenize' do

        it "handles Chinese with punctuation" do
          s = "现在中国的形势是：银行行长"
          expect(@t.tokenize(s).map(&:first)).to eq %w[ 现 在 中 国 的 形 势 是 银 行 行 长 ]
        end

      end

    end

  end
end

