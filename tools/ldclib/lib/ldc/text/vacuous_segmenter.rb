require_relative "segmenter"
module LDC
  module Text

    # this bypasses the actual segmenter, returning each string as a single segment
    class VacuousSegmenter < Segmenter

      def initialize(lang: nil)
        @pass_through_normalizer = PassThroughNormalizer.new
        @type = :ldc_sent_seg
        @lang = lang
      end

      def pass_through_pipe(string)
        [ string ]
      end

    end

  end
end

