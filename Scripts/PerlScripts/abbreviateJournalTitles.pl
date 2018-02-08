#!/usr/bin/perl
#
# Jeremy Van Cleve <jeremy.vancleve@gmail.com>
#
# 2010/12/13: fixed cleanKey function to replace "and" correctly and delete redundant spaces

use strict;
use warnings;
use Getopt::Std;

sub cleanKey {
  my $key = shift;

  # lowercase key
  $key = lc($key);
  # remove leading and trailing spaces from potential key or abbreviation
  $key =~ s/(^\s+)|(\s+$)//g;
  # remove periods
  $key =~ s/\.//g;
  # replace "and" with "&" and delete leading backslash if present
  $key =~ s/\s+and\s+/ & /ig;
  $key =~ s/\\&/&/g;
  # remove leading "the"
  $key =~ s/^the\s+//ig;
  # delete redundant spaces
  $key =~ s/\s+/ /g;

  return $key
}

my @abbrevfiles
  = (
     "Volumes/Dropbox/Dropbox/gitRepos/SourcesOnGitHub/Scripts/journal_abbreviations/abbreviations.txt"
    );

my (%abbrevFK, %abbrevAK, %fullname);
my %opts;

getopts('ima', \%opts);

if (!defined($opts{'i'}) && !defined($opts{'m'}) && !defined($opts{'a'})) {
  print "usage: $0 [opts] args \n";
  print "opts: \n";
  print "\t -i: take titles and return ISO abbreviations\n";
  print "\t -m: take titles and return Medline abbreviations\n";
  print "\t -a: take abbreviations and return titles\n";
  print "args: \n";
  print "\t list of quoted titles or quoted abbreviations\n";
  exit;
}

foreach my $file (@abbrevfiles) {
  open FILE, "<$file" or die "Couldn't open $file\n";

  while (<FILE>) {
    chomp;
    my @pieces = split /[=;]/;

    # no full title or abbreviation
    if ($#pieces < 1) {
      print "!!! no full title or abbreviation for line: $_\n";
      next;
    }

    $pieces[0] =~ s/(^\s+)|(\s+$)//g;
    $pieces[1] =~ s/(^\s+)|(\s+$)//g;

    # create abbreviated title key w/o capitals or periods or leading or trailing spaces.
    my $title_key = $pieces[0];
    $title_key = cleanKey($title_key);

    # if journal hasn't been seen before, add it.
    if (!defined($abbrevFK{$title_key})) {
      # add abbreviation for full title
      $abbrevFK{$title_key} = $pieces[1];
    }

    my $abbrev_key = $pieces[1];
    $abbrev_key = cleanKey($abbrev_key);

    # Check to make sure abbreviation hasn't been seen before either for title replacement; if not add it
    if (!defined($abbrevAK{$abbrev_key})) {
	# add title and abbreviations keys to abbreviation hash and abbreviation to title hash
	$abbrevAK{$abbrev_key} = $pieces[1];
	$fullname{$abbrev_key} = $pieces[0];
      }
    }


  close FILE;
}

# process options for medline or ISO abbreviation
if ($opts{'i'} || $opts{'m'}) {
  foreach my $arg (@ARGV) {
    $arg = cleanKey($arg);
    my $abrv = "";

    if (defined($abbrevFK{$arg})) {
      # set abbreviation based on full title
      $abrv = $abbrevFK{$arg};
    }
    elsif (defined($fullname{$arg})) {
      # if not given full title, assume abbreviation and turn back into
      # full title to find "standard" abbreviation according to abbreviation lists
      if (defined($abbrevFK{cleanKey($fullname{$arg})})) {
	$abrv = $abbrevFK{cleanKey($fullname{$arg})};
      }
    }
    elsif (defined($abbrevAK{$arg})) {
      # all else fails, output old abbreviation
      $abrv = $abbrevAK{$arg};
    }

    if ($opts{'m'}) {
      # remove periods for medline abbreviation
      $abrv =~ s/\.//g;
    }
    print "$abrv\n";
  }
}

# process options for full title
elsif ($opts{'a'}) {
  foreach my $arg (@ARGV) {
    $arg = cleanKey($arg);

    if (defined($fullname{$arg})) {
      # if full title exists, return with added backslash for LaTeX
      my $return_name = $fullname{$arg};
      $return_name =~ s/([^\\])&/$1\\&/g;
      print $return_name . "\n";
    }
    else {
      print "\n";
    }
  }
}
