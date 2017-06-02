#!/usr/bin/perl -w
# Author: Ulf Hermjakob 
# Version 1.0 on March 7, 2017

# This scripts repairs some typical UTF8 encoding errors, deletes some zero-space characters, normalizes non-zero-width spaces.

# Usage: wildeclean.pl < STDIN > STDOUT
# Usage: wildeclean.pl -r < STDIN > STDOUT 2> STDERR     Report statistics to STDERR.


my $windows_repair_p = 0;
my $report_changes_p = 0;
my $delete_chars_p = 1;
my $norm_spaces_p = 1;

%ht = ();

while (@ARGV) {
   $arg = shift @ARGV;
   if ($arg =~ /^-*win/) {
      $windows_repair_p = 1;
   } elsif ($arg =~ /^-*(r|rep|report)$/) {
      $report_changes_p = 1;
   } else {
      print STDERR "Ignoring unrecognized arg $arg\n";
   }
}

sub windows1252_to_utf8 {
   local($s, $norm_to_ascii_p) = @_;

   return $s if $s =~ /^[\x00-\x7F]*$/; # all ASCII

   $norm_to_ascii_p = 1 unless defined($norm_to_ascii_p);
   my $result = "";
   my $c = "";
   while ($s ne "") {
      $n_bytes = 1;
      if ($s =~ /^[\x00-\x7F]/) {
         $result .= substr($s, 0, 1);  # ASCII
      } elsif ($s =~ /^[\xC0-\xDF][\x80-\xBF]/) {
         $result .= substr($s, 0, 2);  # valid 2-byte UTF8
         $n_bytes = 2;
      } elsif ($s =~ /^[\xE0-\xEF][\x80-\xBF][\x80-\xBF]/) {
         $result .= substr($s, 0, 3);  # valid 3-byte UTF8
         $n_bytes = 3;
      } elsif ($s =~ /^[\xF0-\xF7][\x80-\xBF][\x80-\xBF][\x80-\xBF]/) {
         $result .= substr($s, 0, 4);  # valid 4-byte UTF8
         $n_bytes = 4;
      } elsif ($s =~ /^[\xF8-\xFB][\x80-\xBF][\x80-\xBF][\x80-\xBF][\x80-\xBF]/) {
         $result .= substr($s, 0, 5);  # valid 5-byte UTF8
         $n_bytes = 5;
      } elsif ($s =~ /^[\xA0-\xBF]/) {
         $c = substr($s, 0, 1);
         $result .= "\xC2$c";
      } elsif ($s =~ /^[\xC0-\xFF]/) {
         $c = substr($s, 0, 1);
         $c =~ tr/[\xC0-\xFF]/[\x80-\xBF]/;
         $result .= "\xC3$c";
      } elsif ($s =~ /^\x80/) {
         $result .= "\xE2\x82\xAC";  # Euro sign
      } elsif ($s =~ /^\x82/) {
         $result .= "\xE2\x80\x9A";  # single low quotation mark
      } elsif ($s =~ /^\x83/) {
         $result .= "\xC6\x92";      # Latin small letter f with hook
      } elsif ($s =~ /^\x84/) {
         $result .= "\xE2\x80\x9E";  # double low quotation mark
      } elsif ($s =~ /^\x85/) {
         $result .= ($norm_to_ascii_p) ? "..." : "\xE2\x80\xA6";  # horizontal ellipsis (three dots)
      } elsif ($s =~ /^\x86/) {
         $result .= "\xE2\x80\xA0";  # dagger
      } elsif ($s =~ /^\x87/) {
         $result .= "\xE2\x80\xA1";  # double dagger
      } elsif ($s =~ /^\x88/) {
         $result .= "\xCB\x86";      # circumflex
      } elsif ($s =~ /^\x89/) {
         $result .= "\xE2\x80\xB0";  # per mille sign
      } elsif ($s =~ /^\x8A/) {
         $result .= "\xC5\xA0";      # Latin capital letter S with caron
      } elsif ($s =~ /^\x8B/) {
         $result .= "\xE2\x80\xB9";  # single left-pointing angle quotation mark
      } elsif ($s =~ /^\x8C/) {
         $result .= "\xC5\x92";      # OE ligature
      } elsif ($s =~ /^\x8E/) {
         $result .= "\xC5\xBD";      # Latin capital letter Z with caron
      } elsif ($s =~ /^\x91/) {
         $result .= ($norm_to_ascii_p) ? "`" : "\xE2\x80\x98";  # left single quotation mark
      } elsif ($s =~ /^\x92/) {
         $result .= ($norm_to_ascii_p) ? "'" : "\xE2\x80\x99";  # right single quotation mark
      } elsif ($s =~ /^\x93/) {
         $result .= "\xE2\x80\x9C";  # left double quotation mark
      } elsif ($s =~ /^\x94/) {
         $result .= "\xE2\x80\x9D";  # right double quotation mark
      } elsif ($s =~ /^\x95/) {
         $result .= "\xE2\x80\xA2";  # bullet
      } elsif ($s =~ /^\x96/) {
         $result .= ($norm_to_ascii_p) ? "-" : "\xE2\x80\x93";  # n dash
      } elsif ($s =~ /^\x97/) {
         $result .= ($norm_to_ascii_p) ? "-" : "\xE2\x80\x94";  # m dash
      } elsif ($s =~ /^\x98/) {
         $result .= ($norm_to_ascii_p) ? "~" : "\xCB\x9C";      # small tilde
      } elsif ($s =~ /^\x99/) {
         $result .= "\xE2\x84\xA2";  # trade mark sign
      } elsif ($s =~ /^\x9A/) {
         $result .= "\xC5\xA1";      # Latin small letter s with caron
      } elsif ($s =~ /^\x9B/) {
         $result .= "\xE2\x80\xBA";  # single right-pointing angle quotation mark
      } elsif ($s =~ /^\x9C/) {
         $result .= "\xC5\x93";      # oe ligature
      } elsif ($s =~ /^\x9E/) {
         $result .= "\xC5\xBE";      # Latin small letter z with caron
      } elsif ($s =~ /^\x9F/) {
         $result .= "\xC5\xB8";      # Latin capital letter Y with diaeresis
      } else {
         $result .= "?";
      }
      $s = substr($s, $n_bytes);
   }
   return $result;
}

sub register_change {
   local($type, $change) = @_;

   $ht{REPL_COUNT}->{$type}->{$change} = ($ht{REPL_COUNT}->{$type}->{$change} || 0) + 1;
   $ht{REPL_EX_LN}->{$type}->{$change}->{$line_number} = 1;
}

$line_number = 0;
while (<>) {
   $line_number++;

   my $s = $_;
   # correcting UTF8 misencodings due to double application of Latin1-to-UTF converter (2 bytes)
   if ($s =~ /\xC3[\x80-\x9F]\xC2[\x80-\xBF]/) {
      my $result = "";
      while (($pre,$c1,$c2,$post) = ($s =~ /^(.*?)\xC3([\x80-\x9F])\xC2([\x80-\xBF])(.*)$/s)) {
	 my $orig_c1 = $c1;
	 $c1 =~ tr/[\x80-\x9F]/[\xC0-\xDF]/;
         $result .= "$pre$c1$c2";
         $s = $post;
	 &register_change("CHANGE2", "\xC3$orig_c1\xC2$c2 TO $c1$c2") if $report_changes_p;
      }
      $result .= $s;
      $s = $result;
   }
   # correcting UTF8 misencodings due to double application of Latin1-to-UTF converter (3 bytes)
   if ($s =~ /\xC3[\xA0-\xAF]\xC2[\x80-\xBF]\xC2[\x80-\xBF]/) {
      my $result = "";
      while (($pre,$c1,$c2,$c3,$post) = ($s =~ /^(.*?)\xC3([\xA0-\xAF])\xC2([\x80-\xBF])\xC2([\x80-\xBF])(.*)$/s)) {
	 my $orig_c1 = $c1;
	 $c1 =~ tr/[\xA0-\xAF]/[\xE0-\xEF]/;
         $result .= "$pre$c1$c2$c3";
         $s = $post;
	 &register_change("CHANGE3", "\xC3$orig_c1\xC2$c2\xC2$c3 TO $c1$c2$c3") if $report_changes_p;
      }
      $result .= $s;
      $s = $result;
   }

   # correcting conversions of Windows1252-to-UTF8 using Latin1-to-UTF converter
   if ($windows_repair_p && ($s =~ /\xC2[\x80-\x9F]/)) {
      my $result = "";
      while (($pre,$c_windows,$post) = ($s =~ /^(.*?)\xC2([\x80-\x9F])(.*)$/s)) {
         my $c_utf8 = &windows1252_to_utf8($c_windows, 0);
	 $c_utf8 = $c_windows if $c_utf8 eq "?";
         $result .= "$pre$c_utf8";
         $s = $post;
	 &register_change("CHANGE1", "\xC2$c_windows TO $c_utf8") if $report_changes_p;
      }
      $result .= $s;
      $s = $result;
   }

   # delete stuff
   # control chacters (except tab and linefeed), zero-width characters, byte order mark,
   # directional marks, join marks, variation selectors, Arabic tatweel
   if ($delete_chars_p) {
      my $result = "";
      while (($pre,$char,$post) = ($s =~ /^(.*?)([\x00-\x08\x0B-\x1F\x7F]|\C2[\x80-\x9F]|\xD9\x80|\xE2\x80[\x8B-\x8F]|\xEF\xB8[\x80-\x8F]|\xEF\xBB\xBF|\xF3\xA0[\x84-\x87][\x80-\xBF])(.*)$/s)) {
	 $result .= $pre;
	 $s = $post;
	 &register_change("DELETE1", "$char") if $report_changes_p;
      }
      $result .= $s;
      $s = $result;
   }

   # normalize (non-zero-width) spaces
   if ($norm_spaces_p) {
      my $result = "";
      while (($pre,$char,$post) = ($s =~ /^(.*?)(\xC2\xA0|\xE2\x80[\x82-\x8A]|\xE2\x80\xAF|\xE2\x81\x9F)(.*)$/s)) {
	 $result .= "$pre ";
	 $s = $post;
	 &register_change("NORM_SP", "$char") if $report_changes_p;
      }
      $result .= $s;
      $s = $result;
   }
   # no empties
   if ($s =~ /^\s+$/){
       $s = "_\n";
       &register_change("NOZERO", "empty to _") if $report_changes_p;
   }
   print $s;
}

# Report statistics if requested.
if ($report_changes_p) {
   my $total_count = 0;
   foreach $type (sort keys %{$ht{REPL_COUNT}}) {
      foreach $repl (sort { $ht{REPL_COUNT}->{$type}->{$b} <=> $ht{REPL_COUNT}->{$type}->{$a} }
		     keys %{$ht{REPL_COUNT}->{$type}}) {
         $count = $ht{REPL_COUNT}->{$type}->{$repl};
         $total_count += $count;
         @line_numbers = sort { $a <=> $b } keys %{$ht{REPL_EX_LN}->{$type}->{$repl}};
         if ($#line_numbers > 9) {
            @line_numbers = @line_numbers[0..10];
            $line_numbers[10] = "...";
         }
         print STDERR "$type $repl ($count) in lines @line_numbers\n";
      }
      print STDERR "\n";
   }
   print STDERR "Total number of changes: $total_count\n";
}

exit 0;

