require_relative "segmenter"
module LDC
  module Text

    class ExternalSegmenter < Segmenter

      def initialize(lang: nil, segmenter: nil, model: nil)
        @pass_through_normalizer = PassThroughNormalizer.new
        @type = :ldc_sent_seg
        @lang = lang
        raise "no segmenter given" unless segmenter
        raise "no model given" unless model
        @pipe = IO.popen([segmenter, model, '--ignore_newlines'], "r+")
      end

    end

  end
end

