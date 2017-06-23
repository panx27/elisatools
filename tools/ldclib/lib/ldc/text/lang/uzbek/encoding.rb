require 'yaml'
module LDC
  module Text
    module Lang
      module Uzbek

        class Encoding
          attr_accessor :libpath
          def initialize
            @libpath = File.dirname( __FILE__ )
            @charmap = YAML.load File.read "#@libpath/uzb_cyrillic2latin.yaml"
            @unigram_cyril = @charmap["LatinUnigrams"].keys.join('')
            @unigram_latin = @charmap["LatinUnigrams"].values.join('')
          end
          def cyrillic_to_latin( strng )
            latin_strng = strng.gsub( /(?<=^|[ ЫЮЁЭЯУОИЕАыюёэяуоиеа])([Ее])/ ){|e| y = ( e =~ /E$/ ) ? "Й" : "й"; e.prepend y }
            @charmap["LatinBigrams"].each_pair{ |cyr,lat| latin_strng.gsub!( cyr, lat ) }
            latin_strng.tr!( @unigram_cyril, @unigram_latin )
            latin_strng
          end
          def normalize_latin( strng )
            norm_strng = strng.dup
            apostrophes = "'`\u2018\u2019"
            norm_strng.gsub!( /([GOgo])[#{apostrophes}]/ ) { |m| "#{$1}\u02BB" }
            norm_strng.tr!( apostrophes, "\u02BC" )
            norm_strng
          end

          def normalize(string)
            normalize_latin cyrillic_to_latin string
          end

        end

      end
    end
  end
end
