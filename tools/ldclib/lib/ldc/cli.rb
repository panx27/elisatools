require 'ostruct'
require 'optparse'
require 'tmpdir'
require 'parallel'
require_relative 'ldclib'
module LDC
  class CLI

    attr_reader :parser

    def initialize(test=false)
      @test = test
      @file_options = {}
      $options = OpenStruct.new
      @parser = OptionParser.new
      @parser.banner = "\nldclib version #{LDC::LDCLIB::VERSION}"
      yield self
      @parser.on_tail( '-h', '--help', 'show this help message') do
        puts @parser
        puts
        puts "    #{File.basename $0} --man    show the man page"
        puts
        exit
      end
      unless @test
        begin
          @parser.parse!
        rescue OptionParser::InvalidOption => e
          puts
          puts e
          puts @parser
          exit
        end
        if $options.man
          fn = "#{Dir.tmpdir}/#{File.basename($0)}.ldclib_man_page"
          open(fn, 'w') { |f| f.puts @man }
          exec "ronn", "--pipe", "-m", fn
        end
        check_file_options
        @parser
      end
    end

    def banner(banner)
      @parser.banner = banner
    end

    def add_to_banner(banner)
      @parser.banner += banner
    end

    def man(fn)
      # synopsis = @parser.to_s.gsub 'token_parse', '    token_parse'
      @man = File.read(fn).split('__END__').last #.sub "=\n", "=\n## SYNOPSIS\n\n#{synopsis}"
      on "- man show the man page"
    end

    # e.g.:  op "c check-this do some checking"
    # skip short form by using -
    # e.g.:  op "- some-more-checking does more checking"
    # include arg like so:
    # e.g.:  op "C check-this-thing:THING checks the given thing"
    def on(option)
      if option =~ /^([-a-zA-Z])\s+([a-z][-a-zA-Z0-9]+)(:(\w+))?\s+(.+)\Z/
        short_form, long_form, arg, description = $1, $2, $4, $5
        raise "don't use single quotes in the option description" if description.include? "'"
        @file_options[long_form] = nil if arg == 'FILE'
        attribute = long_form.gsub('-', '_')
        code = "@parser.on("
        code << "'-#{short_form}', " unless short_form == '-'
        code << "'--#{long_form}"
        code << " #{arg}" if arg
        code << "', '#{description}') {"
        code << " |x|" if arg
        code << " $options.#{attribute} = "
        code << (arg ? 'x' : 'true')
        code << ' }'
        if @test
          puts code
        else
          eval code
        end
      else
        raise "bad option format: #{option}"
      end
    end

    def set_default_file(option:, fn:)
      @file_options[option.to_s] = fn
    end

    def check_file_options
      @file_options.each do |op, default|
        fn = $options.send op
        if fn
          check_file fn
        elsif default
          check_file default
          $options.send "#{op}=", default
        end
      end
    end

    def check_file(fn)
      abort "file #{fn} doesn't exist" unless File.exists? fn
    end

    def io_pair_batches_sorted_by_size(io_pairs:, jobs:)

      # a batch is a list of files for one process
      batches = Array.new(jobs) { Array.new }

      # sorting by input size allows even distribution across processes
      # options.io_pairs.sort_by { |x| File.size? x.first }.each_with_index do |io_pair, i|
      io_pairs.sort_by { |x| File.size? x.first }.each_with_index do |io_pair, i|
        batches[ i % jobs ] << io_pair
      end

      batches

    end

    def check_output_dir(dir)
      abort "specify output directory" unless dir
      begin
        Dir.mkdir dir unless Dir.exists? dir
      rescue
        abort "failed to create the directory: #{dir}"
      end
    end

    def balance_by_file_size_and_run_in_parallel(ifiles:, ofiles:)
      raise 'no input files' if ifiles.size == 0
      raise 'ifiles and ofiles have different lengths' if ifiles.size != ofiles.size
      files = ifiles.zip ofiles
      if files.size == 1
        [ yield(files) ]
      else
        jobs = $options.jobs.to_i
        jobs = 1 if jobs < 1
        jobs = files.size if jobs > files.size
        batches = io_pair_batches_sorted_by_size io_pairs: files, jobs: jobs
        Parallel.map(batches, :in_processes => jobs) do |batch|
          yield batch
        end
      end
    end

  end

end
