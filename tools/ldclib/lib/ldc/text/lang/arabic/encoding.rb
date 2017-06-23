module LDC
  module Text
    module Lang
      module Arabic

        class Encoding

          def normalize(string)
            insert_arabic_latin_boundary_spaces pres2norm string.dup
          end

          def insert_arabic_latin_boundary_spaces(string)
            string.gsub( /(?<=\p{Arabic})(?=[0-9A-Z])|(?<=[0-9A-Z])(?=\p{Arabic})/i, " " )
          end

# Return an edited copy of a Unicode string such that
# presentation-form Arabic letters are replaced by normal-form letters

  def initialize()
    @sub1to2 = Hash[
                   "[\uFEF5\uFEF6]", "\u0644\u0622", # lig. lam with alef with madda above
                   "[\uFEF7\uFEF8]", "\u0644\u0623", # lig. lam with alef with hamza above
                   "[\uFEF9\uFEFA]", "\u0644\u0625", # lig. lam with alef with hamza below
                   "[\uFEFB\uFEFC]", "\u0644\u0627"  # lig. lam with alef
                  ]

    @trans1to1 = Hash[
                     "\uFB50\uFB51", "\u0671",  # alef wasla
                     "\uFB52-\uFB55", "\u067B", # beeh
                     "\uFB56-\uFB59", "\u067E", # peh
                     "\uFB5A-\uFB5D", "\u0680", # beheh
                     "\uFB5E-\uFB61", "\u067A", # tteheh
                     "\uFB62-\uFB65", "\u067F", # teheh
                     "\uFB66-\uFB69", "\u0679", # tteh
                     "\uFB6A-\uFB6D", "\u06A4", # veh
                     "\uFB6E-\uFB71", "\u06A6", # peheh
                     "\uFB72-\uFB75", "\u0684", # dyeh
                     "\uFB76-\uFB79", "\u0683", # nyeh
                     "\uFB7A-\uFB7D", "\u0686", # tcheh
                     "\uFB7E-\uFB81", "\u0687", # tcheheh
                     "\uFB82\uFB83", "\u068D",  # ddahal
                     "\uFB84\uFB85", "\u068C",  # dahal
                     "\uFB86\uFB87", "\u068E",  # dul
                     "\uFB88\uFB89", "\u0688",  # ddal
                     "\uFB8A\uFB8B", "\u0698",  # jeh
                     "\uFB8C\uFB8D", "\u0691",  # rreh
                     "\uFB8E-\uFB91", "\u06A9", # keheh
                     "\uFB92-\uFB95", "\u06AF", # gaf
                     "\uFB96-\uFB99", "\u06B3", # gueh
                     "\uFB9A-\uFB9D", "\u06B1", # ngoeh
                     "\uFB9E\uFB9F", "\u06BA",  # noon ghunna
                     "\uFBA0-\uFBA3", "\u06BB", # rnoon
                     "\uFBA4\uFBA5", "\u06C0",  # heh with yeh above
                     "\uFBA6-\uFBA9", "\u06C1", # heh goal
                     "\uFBAA-\uFBAD", "\u06BE", # heh doachashmee
                     "\uFBAE\uFBAF", "\u06D2",  # yeh barree
                     "\uFBB0\uFBB1", "\u06D3",  # yeh barree with hamza above
                     "\uFBD3-\uFBD6", "\u06AD", # ng
                     "\uFBD7\uFBD8", "\u06C7",  # u
                     "\uFBD9\uFBDA", "\u06C6",  # oe
                     "\uFBDB\uFBDC", "\u06C8",  # yu
                     "\uFBDD", "\u0677",        # u with hamza above
                     "\uFBDE\uFBDF", "\u06CB",  # ve
                     "\uFBE0\uFBE1", "\u06C5",  # kirghiz oe
                     "\uFBE2\uFBE3", "\u06C9",  # kirghiz yu
                     "\uFBE4-\uFBE7", "\u06D0", # e
                     "\uFBE8\uFBE9", "\u0649",  # alef maksura
                     "\uFBFC-\uFBFF", "\u06CC", # farsi yeh
                     "\uFE74", "\u064D",        # kasratan
                     "\uFE76-\uFE77", "\u064E", # fatha
                     "\uFE78-\uFE79", "\u064F", # damma
                     "\uFE7A-\uFE7B", "\u0650", # kasra
                     "\uFE7C-\uFE7D", "\u0651", # shadda
                     "\uFE7E-\uFE7F", "\u0652", # sukun
                     "\uFE80", "\u0621",        # hamza
                     "\uFE81\uFE82", "\u0622",  # alef with madda above
                     "\uFE83\uFE84", "\u0623",
                     "\uFE85\uFE86", "\u0624",
                     "\uFE87\uFE88", "\u0625",
                     "\uFE89-\uFE8C", "\u0626",
                     "\uFE8D\uFE8E", "\u0627",
                     "\uFE8F-\uFE92", "\u0628",
                     "\uFE93\uFE94", "\u0629",
                     "\uFE95-\uFE98", "\u062A",
                     "\uFE99-\uFE9C", "\u062B",
                     "\uFE9D-\uFEA0", "\u062C",
                     "\uFEA1-\uFEA4", "\u062D",
                     "\uFEA5-\uFEA8", "\u062E",
                     "\uFEA9\uFEAA", "\u062F",
                     "\uFEAB\uFEAC", "\u0630",
                     "\uFEAD\uFEAE", "\u0631",
                     "\uFEAF\uFEB0", "\u0632",
                     "\uFEB1-\uFEB4", "\u0633",
                     "\uFEB5-\uFEB8", "\u0634",
                     "\uFEB9-\uFEBC", "\u0635",
                     "\uFEBD-\uFEC0", "\u0636",
                     "\uFEC1-\uFEC4", "\u0637",
                     "\uFEC5-\uFEC8", "\u0638",
                     "\uFEC9-\uFECC", "\u0639",
                     "\uFECD-\uFED0", "\u063A",
                     "\uFED1-\uFED4", "\u0641",
                     "\uFED5-\uFED8", "\u0642",
                     "\uFED9-\uFEDC", "\u0643",
                     "\uFEDD-\uFEE0", "\u0644",
                     "\uFEE1-\uFEE4", "\u0645",
                     "\uFEE5-\uFEE8", "\u0646",
                     "\uFEE9-\uFEEC", "\u0647",
                     "\uFEED\uFEEE", "\u0648",
                     "\uFEEF\uFEF0", "\u0649",
                     "\uFEF1-\uFEF4", "\u064A"
                    ]
  end

  def pres2norm( ar_str )
    return ar_str unless ( ar_str =~ /[\uFB50-\uFBFF\uFE70-\uFEFC]/ )
    ed_str = ar_str
    for s in @sub1to2.keys
      ed_str.gsub!( /#{s}/, @sub1to2[s] );
    end
    for t in @trans1to1.keys
      ed_str.tr!( t, @trans1to1[t] );
    end
    return ed_str
  end

        end

      end
    end
  end
end

