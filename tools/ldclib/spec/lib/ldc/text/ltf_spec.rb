require 'spec_helper'
require_relative '../../../../lib/ldc/text/ltf'

module LDC
  module Text

    class T
      attr_accessor :total
      def tokens(s)
        beg, total = 0, 0
        s.scan(/\s+|\S+/).map do |x|
          beg = total
          total += x.length
          if x =~ /\S/
            [ x, 'word', beg, x.length ]
          end
        end.compact
      end
    end

    RSpec.describe LTF do

      before :each do
        @ltf = described_class.new
        @doc = Document.new
        @doc.string = "This is one. \nThis is two."
      end

      describe '#to_ltf_xml' do

        it "serializes to ltf xml" do
          @doc.docid = 'docid'
          @doc.create_segmentation :simple
          @doc.tokenize T.new
          expect(@ltf.doc2xml @doc).to eq '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE LCTL_TEXT SYSTEM "ltf.v1.5.dtd">
<LCTL_TEXT>
<DOC id="docid" tokenization="none" grammar="none" raw_text_char_length="26" raw_text_md5="06f9cdf1b7067abe85fef40ca4a72db6">
<TEXT>
<SEG id="segment-0" start_char="0" end_char="11">
<ORIGINAL_TEXT>This is one.</ORIGINAL_TEXT>
<TOKEN id="token-0-0" pos="word" morph="none" start_char="0" end_char="3">This</TOKEN>
<TOKEN id="token-0-1" pos="word" morph="none" start_char="5" end_char="6">is</TOKEN>
<TOKEN id="token-0-2" pos="word" morph="none" start_char="8" end_char="11">one.</TOKEN>
</SEG>
<SEG id="segment-1" start_char="14" end_char="25">
<ORIGINAL_TEXT>This is two.</ORIGINAL_TEXT>
<TOKEN id="token-1-0" pos="word" morph="none" start_char="14" end_char="17">This</TOKEN>
<TOKEN id="token-1-1" pos="word" morph="none" start_char="19" end_char="20">is</TOKEN>
<TOKEN id="token-1-2" pos="word" morph="none" start_char="22" end_char="25">two.</TOKEN>
</SEG>
</TEXT>
</DOC>
</LCTL_TEXT>
'
        end

      end

      describe '#ltf2rsd' do

        it "creates an rsd txt file from ltf" do
          ltf =  '<?xml version="1.0" encoding="UTF-8"?>
<LCTL_TEXT>
<DOC id="docid" tokenization="none" grammar="none">
<TEXT>
<SEG id="segment-0" start_char="0" end_char="11">
<ORIGINAL_TEXT>This is one.</ORIGINAL_TEXT>
<TOKEN id="token-0-0" pos="word" morph="none" start_char="0" end_char="3">This</TOKEN>
<TOKEN id="token-0-1" pos="word" morph="none" start_char="5" end_char="6">is</TOKEN>
<TOKEN id="token-0-2" pos="word" morph="none" start_char="8" end_char="11">one.</TOKEN>
</SEG>
<SEG id="segment-1" start_char="14" end_char="25">
<ORIGINAL_TEXT>This is two.</ORIGINAL_TEXT>
<TOKEN id="token-1-0" pos="word" morph="none" start_char="14" end_char="17">This</TOKEN>
<TOKEN id="token-1-1" pos="word" morph="none" start_char="19" end_char="20">is</TOKEN>
<TOKEN id="token-1-2" pos="word" morph="none" start_char="22" end_char="25">two.</TOKEN>
</SEG>
</TEXT>
</DOC>
</LCTL_TEXT>
'
          expect(@ltf.ltf2rsd ltf).to eq "This is one.\n\nThis is two.\n\n"
        end

      end

      describe '#parse_xml' do

        it "parses ltf xml" do
          analyzer = OpenStruct.new
          analyzer.graph = { 'morphemes' => {} }
          @doc.analyzer = analyzer
          @doc.analyzer.graph['morphemes']['verb'] = { 'strings' => { 'is' => {} } }
          @ltf.parse_xml @doc, '<?xml version="1.0" encoding="UTF-8"?>
<LCTL_TEXT>
  <DOC id="doc" grammar="none">
    <TEXT>
      <SEG id="segment-0" start_char="0" end_char="11">
        <ORIGINAL_TEXT>This is one.</ORIGINAL_TEXT>
        <TOKEN id="token-0-0" pos="word" morph="none" start_char="0" end_char="3">This</TOKEN>
        <TOKEN id="token-0-1" pos="word" morph="is=is:verb" start_char="5" end_char="6">is</TOKEN>
        <TOKEN id="token-0-2" pos="word" morph="none" start_char="8" end_char="11">one.</TOKEN>
      </SEG>
      <SEG id="segment-1" start_char="14" end_char="25">
        <ORIGINAL_TEXT>This is two.</ORIGINAL_TEXT>
        <TOKEN id="token-1-0" pos="word" morph="none" start_char="14" end_char="17">This</TOKEN>
        <TOKEN id="token-1-1" pos="word" morph="none" start_char="19" end_char="20">is</TOKEN>
        <TOKEN id="token-1-2" pos="word" morph="none" start_char="22" end_char="25">two.</TOKEN>
      </SEG>
    </TEXT>
  </DOC>
</LCTL_TEXT>
'
          expect(@doc.string).to eq "This is one. \nThis is two."
          expect(@doc.segments[0].tokens[1].analysis.to_s).to eq 'is=is:verb'
        end

      end

    end

  end
end

