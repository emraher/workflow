
### bibfetch.pl.scpt


These are for the "bibfetch.pl.scpt" on the [mankoff/BibDeskAppleScripts](https://github.com/mankoff/BibDeskAppleScripts).

**"bibfetch.pl" is from [dschoepe/bibfetch](https://github.com/dschoepe/bibfetch)**

```
$ brew install perl
```


Then followed http://triopter.com/archive/how-to-install-perl-modules-on-mac-os-x-in-4-easy-steps/

```
$ sudo perl -MCPAN -e shell


Would you like to configure as much as possible automatically? [yes]


What approach do you want?  (Choose 'local::lib', 'sudo' or 'manual') [local::lib] sudo

perl> o conf init

$ sudo perl -MCPAN -e 'install Bundle::CPAN'

```

sudo perl -MCPAN -e 'install Bundle::Name'

```
$ sudo perl -MCPAN -e 'install URI::Escape'
$ sudo perl -MCPAN -e 'install Web::Scraper'
$ sudo perl -MCPAN -e 'install WWW::Mechanize'
$ sudo perl -MCPAN -e 'install String::Random'
$ sudo perl -MCPAN -e 'install Pod::Usage'
$ sudo perl -MCPAN -e 'install Getopt::Long'

$ sudo perl -MCPAN -e 'install List::Util'
Can't locate object method "install" via package "List::Util" at -e line 1.

```


Added an if loop to scpt file to fix arxiv pdfs.



### abbreviateJournalTitles.pl

For journal title abbreviations script see [Jeremy Van Cleve's page](http://vancleve.theoretical.bio/software/).




