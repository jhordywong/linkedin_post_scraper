# Linkedin Post Scraper

Linkedin post scraper via API which scrape the last X year account's post
HOW TO USE:
1. setup your credential used to scrape at account.json
2. run the script with command:
python post_scraper.py -linkedin_url <acc_we_want_to_scrape>
for e.g:
python post_scraper.py -linkedin_url https://www.linkedin.com/in/fabioaversa/
the default result will only return the post from the last 2 years, if you want to
scrape for another last year, you can do it with this command:
python post_scraper.py -linkedin_url <acc_we_want_to_scrape> -yr <year>
for e.g:
python post_scraper.py -linkedin_url https://www.linkedin.com/in/fabioaversa/ -yr 4