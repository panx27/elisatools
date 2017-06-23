require 'spec_helper'
require_relative '../../../../../../lib/ldc/text/lang/turkish/encoding'

module LDC
  module Text
    module Lang
      module Turkish

        RSpec.describe Encoding do

          before :all do
            @obj = described_class.new
          end

          describe '#normalize_latin' do
            it 'normalizes various apostrophe-like characters to modifier letters, leaving the input unchanged' do
              refstr = "e\u2018f e\u2019n g'o no`go"
              tststr = @obj.normalize_latin( refstr )
              expect( refstr ).to eq "e\u2018f e\u2019n g'o no`go"
              expect( tststr ).to eq "e\u02bcf e\u02bcn g\u02bco no\u02bcgo"
            end
          end

        end

      end
    end
  end
end

