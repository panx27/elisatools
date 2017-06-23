require 'spec_helper'
require_relative '../../../../lib/ldc/text/stream'
require_relative '../../../../lib/ldc/text/document'

module LDC
  module Text

    RSpec.describe Stream do

      before :each do
        @s = described_class.new
        @zip = File.expand_path('../../../../test.ltf.zip', __FILE__)
      end

      describe '#main' do

        # it "raises an error" do
        #   expect { @s.main nil }.to raise_error( /^called/ )
        # end

      end

      describe '#run_over_type' do

        # it "calls main" do
        #   expect { @s.run_over_type(type: 'ltf', zip_files: [@zip]) }.to raise_error(/^called #main/)
        # end

      end

      describe '#run_over_type_helper' do

        before :each do
          @ltf = `unzip -p #@zip`
        end

        it "returns an ltf for type ltf" do
          expect(@s.run_over_type_helper('ltf', @ltf)).to match(/LCTL_TEXT/)
        end

        it "returns an rsd for type rsd" do
          expect(@s.run_over_type_helper('rsd', @ltf)).to eq "test\n"
        end

        it "returns a doc for type docs" do
          expect(@s.run_over_type_helper('docs', @ltf)).to be_instance_of LDC::Text::Document
        end

      end

      describe '#run_over_io_pairs' do

        it "raises if a tokenizer isn't set" do
          expect{@s.run_over_io_pairs([[nil, nil]])}.to raise_error(/don't know what to run/)
        end

        it "calls tokenize" do
          @s.tokenizer = :untokenize
          allow(@s).to receive(:tokenize)
          expect(@s).to receive(:tokenize)
          @s.run_over_io_pairs([[nil,nil]])
        end
      
      end

      describe '#helper1' do

        it "returns ltf" do
          @ltf = `unzip -p #@zip`
          s = Stream.new(tokenizer: TokenizerWord.new)
          expect(s.helper1 'test.rsd.txt', nil, "test\n").to eq @ltf.sub(/tokenization[\w\.]+/, 'none')
        end

      end

      describe '#ltf2rsd' do

        it "returns rsd" do
          @ltf = `unzip -p #@zip`
          expect(@s.ltf2rsd @ltf).to eq "test\n"
        end

      end

      describe '#analyze' do

        it "calls methods on a doc" do
          doc = spy('doc')
          @s.analyze doc
          expect(doc).to have_received('analyzer=')
          expect(doc).to have_received(:analyze_all_segments_accept_and_simplify_first_valid_analysis)
        end

      end

    end

  end
end


