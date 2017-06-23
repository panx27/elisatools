require 'spec_helper'
require_relative '../../../../lib/ldc/text/string_mixin'

module LDC
  module Text

    RSpec.describe Segmenter do

      before :each do
        @segmenter = described_class.new type: nil
      end

      describe '#punkt' do

        it "produces sentxml from text" do
          # todo: keeping punkt in memory should be possible
          # loading punkt is two slow for continous testing, but uncomment the following line to test
          # @segmenter = described_class.new type: :punkt, lang: 'eng'
          # and comment out the following line
          allow(@segmenter).to receive(:segment_with_punkt).and_return( [ "This is a test sentence.", "This is another."] )
          s = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<doc>\n  <p>\n"
          s << "    <segment id=\"segment-0\">This is a test sentence.</segment>\n"
          s << "    <segment id=\"segment-1\">This is another.</segment>\n  </p>\n</doc>\n"
          input = "This is a test sentence.  This is another."
          expect(@segmenter.punkt(string: input)).to eq s
        end

        it "produces sentxml from xml" do
          # todo: keeping punkt in memory should be possible
          # loading punkt is two slow for continous testing, but uncomment the following line to test
          # @segmenter = described_class.new type: :punkt, lang: 'eng'
          # and comment out the following line
          allow(@segmenter).to receive(:segment_with_punkt).and_return( [ "This is a test sentence.", "This is another."] )
          s = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<doc>\n<body>\n<p>\n"
          s << "<segment id=\"segment-0\">This is a test sentence.</segment>\n"
          s << "<segment id=\"segment-1\">This is another.</segment>\n</p>\n</body>\n</doc>\n"
          input = "<doc>\n<body>\nThis is a test sentence.  This is another.\n</body>\n</doc>\n"
          expect(@segmenter.punkt(string: input, xpath: '//body/text()')).to eq s
        end

      end

    end

  end
end

 