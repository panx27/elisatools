#!/usr/bin/env ruby

=begin

Thin wrapper for performing sentence segmentation.

usage:

  create_rsd.rb [language] [segmenter] [model] [ input1 input2 ... ]

example:

  ldclib/bin/create_rsd.rb eng sent_seg/sentseg-pipe.py sent_seg/models/basic.pkl.gz test.txt

The above example assumes the present working directory is the tools directory in the package,
and that there is an input file called test.txt.  The result would be files test.rsd.txt and
test.psm.xml in the same directory.  See below for acceptable language codes.  See the
segmenter documentation about training models.  Input files must be plain text with .txt
extension or XML with .xml extension.

RSD (Raw Source Data) is plain text, but by convention has been normalized and sentence segmented.
This script uses the ldclib code to perform that normalization and call out to the sentence
segmenter included in sent_seg.  If the input is XML, the text is extracted first.  The text
of the document is then segmented and turned into Sentence XML, which has doc, p, and segment
tags.  The sentence XML is then split into RSD and PSM (see ???), which are written to disk.

Some languages have special normalization that is performed on them based on the language
code given as an argument.  You can find this code here:

  ldclib/lib/ldc/text/lang

Any number of input files can be given; .txt and .xml files are selected and others
are ignored.  Output files have .rsd.txt and .psm.xml extensions, and will also
change an initial "txt" or "xml" in the path to "rsd" and "psm" if the input and
output files are gathered in type specific directories (this is not required).
See the lines below that begin with "open".

=end


require_relative '../lib/ldc/text/external_segmenter'
require_relative '../lib/ldc/text/rsd_stream2'

LANGS_FOR_RSD = %w[ amh som cmn eng fas hun rus spa vie ara yor uzb tur hau ]

# includes normalization, sentence segmentation, rsd creation, psm creation
def create_rsd(additions:, lang:, input_type:)
  if LANGS_FOR_RSD.include? lang
    segmenter = ARGV[1]
    model = ARGV[2]
  else
    raise "unknown language: #{lang}"
  end
  # see lib/ldc/text/segmenter.rb
  seg = LDC::Text::ExternalSegmenter.new lang: lang, segmenter: segmenter, model: model
  xpath = input_type == 'xml' ? '//text()' : nil  # non-nil xpath triggers extraction from xml
  stream = LDC::Text::RSDStream2.new segmenter: seg, xpath: xpath, lang: lang
  additions.each do |fn|
    xml = LDC::Text::SentXML.new File.basename(fn)
    xml.rsd_name = File.basename(fn)
    input = File.read fn
    begin
      # see lib/ldc/text/rsd_stream2.rb
      rsd, psm = stream.create_rsd_psm fn, input
      open(fn.sub( /#{input_type}\z/, 'rsd.txt' ).sub( /^#{input_type}/, 'rsd' ), 'w') { |f| f.puts rsd }
      open(fn.sub( /#{input_type}\z/, 'psm.xml' ).sub( /^#{input_type}/, 'psm' ), 'w') { |f| f.puts psm }
    rescue EOFError => e
      STDERR.puts "#{fn} failed segmentation"
      seg = LDC::Text::ExternalSegmenter.new lang: lang, segmenter: segmenter, model: model
    end
  end
end

# run separately over the two input types; ignore anything that's not .txt or .xml
%w[ txt xml ].each do |input_type|
  fns = ARGV.select { |x| x =~ /\.#{input_type}\z/ and File.exists? x }
  create_rsd additions: fns, lang: ARGV[0], input_type: input_type
end

