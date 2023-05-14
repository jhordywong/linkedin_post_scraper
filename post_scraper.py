from linkedin_api import Linkedin
import json
from datetime import datetime
import sqlite3
from services import logger
from datetime import datetime, timedelta, date
import re
from typing import List
import pandas as pd
import requests
from linkedin_api.client import ChallengeException
from dateutil.relativedelta import relativedelta
import argparse


class LinkedInPostScraper:
    def __init__(self):
        pass
        # self.client = self.linkedin_client()

    def _db_engine(self):
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        db_name = "post.db"
        conn = sqlite3.connect(db_name)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS scrapped_post (
            organization_name DATATYPE TEXT,
            startup_uuid DATATYPE TEXT,
            founder_name DATATYPE TEXT,
            linkedin_url DATATYPE TEXT,
            is_scrapped DATATYPE INTEGER,
            is_scrapped_profile DATATYPE INTEGER
        )"""
        )
        return conn, cursor

    def linkedin_client(self, proxy: str):
        with open("account.json", "r") as f:
            account = json.load(f)

        email = account["email"]
        password = account["password"]
        return Linkedin(
            email,
            password,
            # refresh_cookies=True,
            proxies={"http": proxy},
        )

    def get_proxy(self):
        proxy_url = "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        proxy_response = requests.get(proxy_url)
        proxies = [x for x in proxy_response.text.split("\n") if x is not None]
        return proxies

    def scrape_post(self, linkedin_url: str, last_x_year: int = 2):
        proxies = self.get_proxy()
        for proxy in proxies:
            try:
                client = self.linkedin_client(proxy)
                idx = -1
                if linkedin_url.endswith("/"):
                    idx = -2
                public_id = linkedin_url.split("/")[idx]
                logger.info(f"SCRAPING POST FOR ACCOUNT WITH PUBLIC ID {public_id}")
                scrapped_post_raw = client.get_profile_posts(
                    public_id=public_id, post_count=2000,
                )
                prefix_post_url = "https://www.linkedin.com/feed/update/"
                with open(f"test2.json", "w") as f:
                    json.dump(scrapped_post_raw, f)
                scrapped_post_clean = [
                    {
                        "name": s["actor"]["name"]["text"],
                        "content_of_the_post": self.get_content_text(s),
                        "content_media": self.get_media(s),
                        "raw_date": s["actor"]["subDescription"]["text"],
                        "date": self.datepost_converter(
                            s["actor"]["subDescription"]["text"]
                        ),
                        "post_url": prefix_post_url + s["updateMetadata"]["urn"],
                    }
                    for s in scrapped_post_raw
                ]
                account_name = scrapped_post_clean[0]["name"]
                filename = f"linkedin_post_of_{account_name}"
                scrapped_post_cleaned = self.cleaned_data(
                    scrapped_post_clean, last_x_year
                )
                self._save_to_csv(scrapped_post_cleaned, filename)
                with open(f"raw_data.json", "w", encoding="utf-8-sig") as f:
                    json.dump(scrapped_post_clean, f)
                logger.info(f"SCRAPING COMPLETED, SAVED TO {filename}")
                break
            except ChallengeException as e:
                logger.warning("CAPTCHA DETECTED, RELOGIN WITH OTHER PROXY...")
                continue

    def cleaned_data(self, scrapped_data: List, last_x_year: int = 2):
        clean_data = []
        for data in scrapped_data:
            raw_date = data["raw_date"]
            if "yr" in raw_date:
                yr_num = re.findall(r"\d+", raw_date)[0]
                if int(yr_num) <= int(last_x_year):
                    data.pop("raw_date")
                    data.pop("name")
                    clean_data.append(data)
            else:
                data.pop("raw_date")
                data.pop("name")
                clean_data.append(data)
        return clean_data

    def get_content_text(self, input_dict: dict):
        if "commentary" in input_dict:
            return (
                input_dict["commentary"]["text"]["text"]
                .replace("\n", "")
                .replace('"', "")
            )
        elif "resharedUpdate" in input_dict:
            return (
                input_dict["resharedUpdate"]["commentary"]["text"]["text"]
                .replace("\n", "")
                .replace('"', "")
            )
        else:
            return None

    def get_media(self, input_dict: dict):
        if (
            "content" in input_dict
            and "com.linkedin.voyager.feed.render.ImageComponent"
            in input_dict["content"]
        ):
            return (
                input_dict["content"][
                    "com.linkedin.voyager.feed.render.ImageComponent"
                ]["images"][0]["attributes"][0]["vectorImage"]["rootUrl"]
                + input_dict["content"][
                    "com.linkedin.voyager.feed.render.ImageComponent"
                ]["images"][0]["attributes"][0]["vectorImage"]["artifacts"][-1][
                    "fileIdentifyingUrlPathSegment"
                ]
            )
        else:
            return None

    def datepost_converter(self, raw_date: str):
        current_date = datetime.now()
        posted_date = current_date.strftime("%B-%Y")
        date_created = re.findall(r"\d+", raw_date)[0]
        if "mo" in raw_date:
            substracted_date = current_date - relativedelta(months=int(date_created))
        elif "yr" in raw_date:
            substracted_date = current_date - relativedelta(years=int(date_created))
        else:
            substracted_date = current_date
        posted_date = date(substracted_date.year, substracted_date.month, 1).strftime(
            "%B-%Y"
        )
        return posted_date

    def _save_to_csv(self, data: List, filename: str):
        df = pd.DataFrame(data)
        df.to_csv(f"{filename}.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-linkedin_url")
    parser.add_argument("-yr", default=2)
    args = parser.parse_args()

    Scraper = LinkedInPostScraper()
    Scraper.scrape_post(args.linkedin_url, args.yr)
