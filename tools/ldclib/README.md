ldclib
======

This is a snapshot of ldclib specifically made to facilitate generic
segmentation and tokenization.  The first executable is token_parse.rb, and
its man page can be seen with (assuming ruby is installed, see below):

    bundle exec bin/token_parse.rb --man

A brief help is available with -h.  This tool handles tokenization and
conversion of RSD into LTF XML.  Our generic tokenization parameters (i.e. a
file that can be cited as the "-t" / "--tokenization" option parameter) are
included in the parent directory in a yaml file:

         tokenization_parameters.v4.0.yaml

Note that when these tools are included as part of particular language packs,
the tokenization parameters file may be tailored distinctly to the language
being presented in each pack.

To bridge the gap between the token_parse.rb executable and the sentence
segmenter also included in this package (in tools/sent_seg), there is a second
executable included, which is run as follows:

    bundle exec bin/create_rsd.rb [args]

See the comments at the top of that executable for usage.

# Installation

These libraries are written in Ruby and take advantage of the Ruby ecosystem.
The end user need not know Ruby, but should be comfortable with Unix-like
systems.  A system where others are already using Ruby may make the process
smoother.  If you don't yet have Ruby, RVM (Ruby Version Manager) is a common
way to install Ruby, and we direct you there:

    http://rvm.io/

A "gem" is a Ruby library packaged in a particular manner.  This
distribution is not a gem, so you simply run the code from its present
location.  However, we take advantage of publically available gems.
One gem is called Bundler:

    http://bundler.io/

Bundler helps you manage other gems.  Install bundler like so:

    gem install bundler

Bundler can then manage other dependencies for you.  There is a file called
Gemfile which lists other gems required by this distribution, and Bundler will
install them for you like so:

    bundle install

Bundler will also force other programs to use this inventory of gems, which is
wise if you're not familiar with Ruby or the exact operation of this (or any)
code base.  So for example:

    bundle exec bin/token_parse.rb -h

runs "bin/token_parse.rb -h" in the context of these gems.  We will try to
always prepend "bundle exec", although strictly speaking it's not necessary to
run code, just a wise precaution.

This code has been tested with Ruby 2.3.0, and recent, if not the
latest, versions of the necessary gems.

# Testing

An Rspec test suite is available in the "spec" directory, and can be run as
follows from the root of the package:

    bundle exec rspec spec

Jonathan Wright
jdwright@ldc.upenn.edu
2016-05-17 10:13:37 -0400

