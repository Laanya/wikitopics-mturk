#!/usr/bin/env perl

use List::Util 'shuffle';
use URI::Escape;

if (scalar @ARGV != 2) {
	die "Usage: $0 language date";
}

$lang = $ARGV[0];
$date = $ARGV[1];
$year = substr $date, 0, 4;
$wikitopics_path = $ENV{'WIKITOPICS'};
$topic_path = "$wikitopics_path/data/topics/$lang/$year/$date.topics";
$articles_path = "$wikitopics_path/data/articles/$lang/$year/$date";
$first_path = "$wikitopics_path/data/sentences/first/$lang/$year/$date";

$no_articles = 12;

print "date,";

for ($i=0; $i<$no_articles; $i++) {
	print "article$i,trending_score$i,lead_sentence$i,lead_section$i";
	if ($i < $no_articles-1) {
		print ",";
	}
}
print "\n";

@articles = ();

sub escape_for_csv {
	chomp;
	s/,/&#44;/g;
	s/&/&amp;/g;
	s/>/&gt;/g;
	s/</&lt;/g;
	s/"/&quot;/g;
	s/'/&#39;/g;
	return $_;
}

$counter = 1;

sub print_articles {
	@articles = shuffle(@articles);
	$positives_path = "$wikitopics_path/data/controls/$lang/$year/$date/positive.sentences";
	$negatives_path = "$wikitopics_path/data/controls/$lang/$year/$date/negative.sentences";

	open POSITIVES_FILE, "<$positives_path";
	open NEGATIVES_FILE, "<$negatives_path";

	@positives = ();
	@negatives = ();
	while (<POSITIVES_FILE>) {
            $line = escape_for_csv($_);
	    push @positives, $line;
	}

	while (<NEGATIVES_FILE>) {
	    $line = escape_for_csv($_);
	    push @negatives, $line;
	}

	close POSITIVES_FILE;
	close NEGATIVES_FILE;

	$positive_counter = 0;
	$negative_counter = 0;

	while ($#articles>= 0) {
	        print "$date,";
		for ($i=0; $i<11 && $#articles + 1>=0; $i++) {
		    if ($i < 10) {
		        $_ = shift @articles;
			/([^ ]+) .+/;
			$file = uri_escape($1, "^A-Za-z0-9\-\. _~\%");
			$sentences_path = "$articles_path/$file.sentences";
			$tags_path = "$articles_path/$file.tags";
			#$first_sentences_path = "$first_path/$file.sentences";
			$title = escape_for_csv($_);
			$title =~ s/ /,/;
			$title =~ s/_/ /g;
			
			if ((-e "$sentences_path") && (-e "$tags_path")) { # print the first paragraph
			        print "$title,";
				open ARTICLE_FILE, "<$sentences_path";
				open TAG_FILE, "<$tags_path";
				#open FIRST_FILE, "<$first_sentences_path";
				#while (<FIRST_FILE>) {
				#        $first = escape_for_csv($_);
				#	$length = length($first) - 2;
				#	$first = substr($first, 2, $length);
				#	print "$first,";
				#}
				$first_sentence_bool = 1;
				while (<ARTICLE_FILE>) {
					chomp;
					$sentence = escape_for_csv($_);
					$tag = <TAG_FILE>;
					chomp $tag;
					if ($first_sentence_bool) {
						print "$sentence,";
						$first_sentence_bool = 0;
					}
					if ($tag eq "Sentence" || $tag eq "LastSentence") {
						print "$sentence";
						if ($tag eq "LastSentence") {
							last;
						} else {
							print " ";
						}
					}
				}
				close TAG_FILE;
				close ARTICLE_FILE;
				close FIRST_FILE;
			}
			else {
			    print ",,,";
			}
			if ($i < $no_articles-1) {
				print ",";
			}
		    }
		    else {
			if ($positive_counter >= scalar(@positives)) {
			    $positive_counter = 0;
			}
			
			($pos_title, $pos_trending_score, $pos_first_sent, $pos_first_paragraph) = split(/\s*\t\s*/, $positives[$positive_counter]);

			$positive_counter++;

			print "$pos_title,$pos_trending_score,$pos_first_sent,$pos_first_paragraph,";

		        if ($negative_counter >= scalar(@negatives)) {
				$negative_counter = 0;
                        }

                        ($neg_title, $neg_trending_score, $neg_first_sent, $neg_first_paragraph) = split(/\s*\t\s*/, $negatives[$negative_counter]);

                        $negative_counter++;


                        print "$neg_title,$neg_trending_score,$neg_first_sent,$neg_first_paragraph";
		    }
	        }
		print "\n";
	}
}

open TOPIC_FILE, "<$topic_path";
while (<TOPIC_FILE>) {
    /([^ ]+) .+/;
    $file = uri_escape($1, "^A-Za-z0-9\-\. _~\%");
    $sentences_path = "$articles_path/$file.sentences";
    $tags_path = "$articles_path/$file.tags";
    if ((-e "$sentences_path") && (-e "$tags_path")) { # print the first paragraph
	push @articles, $_;
    }
}
close TOPIC_FILE;

@articles = shuffle(@articles);
print_articles;
