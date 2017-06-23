#!/usr/bin/env ruby
require 'yaml'
require 'zip'
require_relative '../lib/ldc/cli'
require_relative '../lib/ldc/text/stream'
require_relative '../lib/ldc/text/document'
require_relative '../lib/ldc/text/tokenizer'

cli = LDC::CLI.new do |op|
  op.add_to_banner "

token_parse.rb -t [params] -i [input] -o [output]
token_parse.rb -t [params] [inputlist1 inputlist2 ...]
ls | token_parse.rb -t [params]

"
  # op.on "- db:FILE sqlite file for storing morphemes"
  op.on "i input:FILE input file to parse, or - for STDIN"
  op.on "o output:OUT output file"
  op.on "t tokenization:FILE file containing tokenization parameters"
  op.on '- debug debugging output'
  # op.on '- debug debug the parsing process'
  # op.on '- read-cache yaml file with cached analyses'
  # op.on '- save-cache:FILE save cache to yaml file with given name'
  op.on "- untokenize create a text file compatible with an LTF file"
  # op.on "S suppress-text-attributes suppress the attributes on the TEXT element of LTF"
  op.on "j jobs:NUM number of concurrent processes; defaults to 2"
  # op.on "- db:SQL save tokens in sqlite"
  op.on "- secondary:FILE uses a secondary stream of tokens to further tokenize"
  op.parser.on( "--diff TYPE", [ :ltf ], 'do a diff' ) do |t|
    $options.diff = t
  end
  op.on "- tokenization2:FILE diff two tokenizations"
  op.man File.absolute_path __FILE__
end

abort "don't use --untokenize with -t" if $options.untokenize and $options.tokenization
abort "you must use -t|--tokenization as well" if $options.tokenization2 and not $options.tokenization

if $options.input and $options.output
  ifiles, ofiles = [ $options.input ], [ $options.output ]
elsif $options.input or $options.output
  abort "Please use both -i and -o together (not just one alone)"
elsif ARGV.size == 0 and $stdin.tty?
  abort "Please pipe or name a list of rsd.txt files to do, or use '-i infile -o outfile'"
else
  ifiles = ARGF.readlines.map do |i|
    i.chomp!
    abort "input file #{i} doesn't exist" unless File.exists? i
    i
  end
  ofiles = if $options.untokenize # reverse the typical pattern
    ifiles.map { |i| i.gsub('ltf', 'rsd').sub(/(?:\.xml)?$/, '.txt') }
  else
    ifiles.map { |i| i.gsub('rsd', 'ltf').sub(/(?:\.txt)?$/, '.xml') }
  end
end

stream = LDC::Text::Stream.new(
  tokenizer: ($options.untokenize ? :untokenize : $options.tokenization),
  diff: $options.diff,
  # when given two different tokenization parameter files, compare the results (just tokens and types)
  tokenizer2: $options.tokenization2,
  secondary: $options.secondary
)

cli.balance_by_file_size_and_run_in_parallel(ifiles: ifiles, ofiles: ofiles) do |batch|

  stream.run_over_io_pairs batch

end.flatten.compact.each do |result|
  puts result
end

__END__
token_parse.rb(1) -- handles tokenization and related tasks
========

## SYNOPSIS

token_parse.rb -t [params] -i [input] -o [output]

token_parse.rb -t [params] [inputlist1 inputlist2 ...]

ls | token_parse.rb -t [params]

## DESCRIPTION

token_parse.rb is a tokenization tool.  It tokenizes its input and produces
LTF as output, an XML format that includes segmentation and tokenization
markup.  The tool assumes line based segmentation in the input, rather than determining boundaries.  Tokenization is preformed based on
parameters provided in a separate file.  There are three modes of
operation for tokenization, regarding IO:  specifying single files, providing files that contain lists of input files, and providing input file names
on STDIN.  The later two modes create output file names by changing the extension of input file names. 

## USE

token_parse.rb -t [params] -i [input] -o [output]

This processes a single input file, allowing precise naming of the output file.

token_parse.rb -t [params] [inputlist1 inputlist2 ...]

Remaining command line arguments are assumed to be files that contain lists of input file names.
Output file names are created by replacing .rsd.txt with .ltf.xml.

ls | token_parse.rb -t [params]

If no command line arguments remain, STDIN is read for input files.  Output file names are created by
replacing .rsd.txt with .ltf.xml.

## OPTIONS

* `--diff ltf`:
perform a diff an existing LTF file, rather than writing one.  works on the three tokenization modes

* `-i`, `--input`:
specify a single input file, must be used with -o

* `-j`, `--jobs`:
specify the number of processes to run in parallel

* `-o`, `--output`:
specify a single output file, must be used with -i

* `-t`, `--tokenization`:
perform tokenization

* `--tokenization2`:
specify a second tokenization parameters file, for doing a diff.  use with -t

* `--untokenize`:
convert LTF back into RSD



