require 'spec_helper'
require_relative '../../../../../../lib/ldc/text/lang/uzbek/encoding'

module LDC
  module Text
    module Lang
      module Uzbek

        RSpec.describe Encoding do

          before :all do
            @obj = described_class.new
          end

          describe '#cyrillic_to_latin' do
            it 'returns a non-Cyrillic string unmodified' do
              test = "THIS, `is' \"A\"; test?! 543-2.1+#/<*>=[]{}_$@%~(:^|)"
              expect( @obj.cyrillic_to_latin( test )).to eq test
            end
            it 'converts Cyrillic characters to their intended Latin equivalents, leaving the input unchanged' do
              refmap = File.read "#{@obj.libpath}/uzb_cyrillic2latin.yaml"
              tstmap = @obj.cyrillic_to_latin( refmap )
              n_ref_pairs = refmap.scan( /\n *\p{Cyrillic}: [A-Za-z\u02bb\u02bc]{1,2}/ ).size
              n_tst_pairs_noY = tstmap.scan( /\n *(\p{Letter}+): \1/ ).size
              n_tst_pairs_withY = tstmap.scan( /\n *y(\p{Letter}): \1/ ).size
              expect( n_ref_pairs == ( n_tst_pairs_noY + n_tst_pairs_withY )).to be true
            end
            it 'normalizes various apostrophe-like characters to modifier letters, leaving the input unchanged' do
              refstr = "e\u2018f e\u2019n g'o no`go"
              tststr = @obj.normalize_latin( refstr )
              expect( refstr ).to eq "e\u2018f e\u2019n g'o no`go"
              expect( tststr ).to eq "e\u02bcf e\u02bcn g\u02bbo no\u02bbgo"
            end
          end

        end

      end
    end
  end
end

