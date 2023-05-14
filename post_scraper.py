from linkedin_api import Linkedin
import json
from datetime import datetime
import sqlite3
from services import logger
from datetime import datetime
import re
from typing import List
import csv
import pandas as pd
import charade


class LinkedInPostScraper:
    def __init__(self):
        self.client = self.linkedin_client()

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

    def linkedin_client(self):
        with open("account.json", "r") as f:
            account = json.load(f)

        email = account["email"]
        password = account["password"]
        return Linkedin(
            email,
            password,
            # refresh_cookies=True,
            proxies={"http": "159.203.84.241:3128"},
        )

    def scrape_post(self, linkedin_url: str):
        idx = -1
        if linkedin_url.endswith("/"):
            idx = -2
        public_id = linkedin_url.split("/")[idx]
        logger.info(f"PUBLIC ID {public_id}")
        scrapped_post_raw = self.client.get_profile_posts(public_id=public_id)
        prefix_post_url = "https://www.linkedin.com/feed/update/"
        scrapped_post_clean = [
            {
                "content_of_the_post": s["commentary"]["text"]["text"]
                .replace("\n", "")
                .replace('"', ""),
                "content_media": self.get_media(s),
                "date": self.datepost_converter(s["actor"]["subDescription"]["text"]),
                "post_url": prefix_post_url + s["updateMetadata"]["urn"],
                "scrapped_at": datetime.now().strftime("%B-%Y"),
            }
            for s in scrapped_post_raw
        ]
        with open(f"test.json", "w", encoding="utf-8-sig") as f:
            json.dump(scrapped_post_clean, f)
        with open(f"test2.json", "w") as f:
            json.dump(scrapped_post_raw, f)

    def get_media(self, input_dict: dict):
        if "content" in input_dict:
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

    def detect_and_convert_text(self, input_string: str):
        encoding = charade.detect(input_string)["encoding"]
        encoded_string = input_string.encode(encoding)
        return encoded_string.decode(encoding)

    def datepost_converter(self, raw_date: str):
        current_date = datetime.now()
        if "d" or "w" in raw_date:
            date = current_date.strftime("%B-%Y")
        elif "mo" in raw_date:
            month_created = re.findall(r"\d+", raw_date)
            # Subtract the specified number of months from the current date
            two_months_ago = current_date - datetime.timedelta(months=month_created)

            # Get the month and year of the date 2 months ago
            two_months_ago_month = two_months_ago.month
            two_months_ago_year = two_months_ago.year

            # Format the output string
            date = datetime.date(two_months_ago_year, two_months_ago_month, 1).strftime(
                "%B-%Y"
            )

            # Print the output string
            print(date)
        return date

    def _save_to_csv(self, data: List, filename: str):
        df = pd.DataFrame(data)
        df.to_csv(f"{filename}.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    Scraper = LinkedInPostScraper()
    Scraper.scrape_post("https://www.linkedin.com/in/fabioaversa/")
