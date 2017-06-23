require 'spec_helper'
module LDC
  module Text

    RSpec.describe Token do

      before :each do
        @token = described_class.new offset: 1, token: 'blah'
      end

      describe '#string' do

        it "returns the token string" do
          doc = OpenStruct.new
          doc.string = " blah "
          @token.document = doc
          expect(@token.string).to eq "blah"
        end

      end

      describe '#to_quad' do

        it "returns the quad structure" do
          doc = OpenStruct.new
          doc.string = " blah "
          @token.document = doc
          expect(@token.to_quad).to eq [ 'blah', nil, 1, 4 ]
        end

      end          

    end

  end
end


