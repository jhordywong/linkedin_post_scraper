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
import openai
from time import sleep
from datetime import datetime
from revChatGPT.V1 import Chatbot


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
                        "number_of_likes": s["socialDetail"][
                            "totalSocialActivityCounts"
                        ]["numLikes"],
                        "number_of_comments": s["socialDetail"][
                            "totalSocialActivityCounts"
                        ]["numComments"],
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

    def rewrite_content(self, content: str = None):
        chatbot = Chatbot(
            config={
                # free
                # "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJqaG9yZHlAZGVsbWFuLmlvIiwiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsidXNlcl9pZCI6InVzZXItdExOV1Z1bDdtSmxkSUJlbVZvTHZ0ZGpKIn0sImlzcyI6Imh0dHBzOi8vYXV0aDAub3BlbmFpLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExMzIyMzk1NDM3NjUyNzk1MTEyMSIsImF1ZCI6WyJodHRwczovL2FwaS5vcGVuYWkuY29tL3YxIiwiaHR0cHM6Ly9vcGVuYWkub3BlbmFpLmF1dGgwYXBwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE2ODQ4OTcyNjAsImV4cCI6MTY4NjEwNjg2MCwiYXpwIjoiVGRKSWNiZTE2V29USHROOTVueXl3aDVFNHlPbzZJdEciLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG1vZGVsLnJlYWQgbW9kZWwucmVxdWVzdCBvcmdhbml6YXRpb24ucmVhZCBvcmdhbml6YXRpb24ud3JpdGUifQ.eZJQrZVYuO4CoLjaVHGptxkxBRn5nAmPRVAFJ1ZyPOzfArTRchKT6x3uJYCoo-MQ9Yi4iei0Wwhvb2BEOVYsP_AdUFwvG_v2XLx2JKO4AeUFaAZmKc4u_oO8d8_ycr0yFeAmuV8P_FcGo-nD8mtVYs4QvO0Hv1l-kuKLNQjG1VZVbxOBYK3nq2F9aA6m2bjmfu-_yCvvFTQiTd1uGRC-4suMrSHfvij7kctEVeUS0j9jh-x7DOkf691xRpcdRcb1x-9w5rgOi9K1ZahX9vl6WHXI2BnQ34GheoDl9eSWCf4l_v_2yJkNpfapHM9jXsWWdxmhDffu23yEgYPiobojAw",
                # paid
                "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJlZmZlY3RpdmVoaXJpbmdAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsidXNlcl9pZCI6InVzZXItaG1TVlF4MWtBaWtBTm90UDBZUlNvYU5yIn0sImlzcyI6Imh0dHBzOi8vYXV0aDAub3BlbmFpLmNvbS8iLCJzdWIiOiJhdXRoMHw2NDZmNmIzM2RiMzM2NjMwYjQ3OGJjM2YiLCJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSIsImh0dHBzOi8vb3BlbmFpLm9wZW5haS5hdXRoMGFwcC5jb20vdXNlcmluZm8iXSwiaWF0IjoxNjg1MDIzNjQxLCJleHAiOjE2ODYyMzMyNDEsImF6cCI6IlRkSkljYmUxNldvVEh0Tjk1bnl5d2g1RTR5T282SXRHIiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCBtb2RlbC5yZWFkIG1vZGVsLnJlcXVlc3Qgb3JnYW5pemF0aW9uLnJlYWQgb3JnYW5pemF0aW9uLndyaXRlIn0.QoxH6cWWVFkCVs0oT2sVqHl4dxOlnUegdps9BEXYtG9WZeGm9XfiZJFCKjM0mpYCCak4xRCx4gXG8wMmC6kG3_KoVxhy0wAx1UlhWH0g6KNU38S5m_TnRoe3B19NWMryi-Z8vYuMutkxWUMs6qjgeg6v9ccZCMLErmcc19vRBTWhxaZ46JTOv-fgBy-gixvBCXuwCUUMiA9zbUQ8BPKw5rKblWkDrobyFBTR1sj-xgQWt8pNkRcJRgvE-pwssx7j5gI3EHxS5tEh5NwT_R7E8lurHEUGeGANJteU-2yNy1ELLq3vq65kTd-BG7JfN6vnjDI0QaxwnyXmVwBY-IfuPg",
                "model": "gpt-4-browsing",
                "disable_history": True,
            }
        )
        prompt = """Rewrite the following text in three different ways. 

        For the first version, use a professional and friendly tone. This is for an audience of adults. Use a Grade 3 readability level. 

        For the second version, use a conversational and clear tone. This is for an audience of young people. Use a Grade 4 readability level. Include Emoji when relevant. 

        For the third version, use a clear and concise tone. This is for an audience of entrepreneurs looking to understand the core idea. Use a Grade 4 readability level.

        Follow these formatting rules:
        1. Use a style to highlight the author's own experience instead of lecturing. Use ""I"" as much as possible rather than ""You"" 
        2. Write each sentence as a new paragraph and include an additional return space.
        3. Bold the critical parts of each text using the ""Math sans bold""        Unicode font.
        4. At the end of each, include the jigsaw emoji as a signature on a new paragraph.


        
        {}
        """.format(
            content
        )
        response = ""
        prev_text = ""
        for data in chatbot.ask(prompt):
            response = data["message"]

            # for streaming
            # message = data["message"][len(prev_text) :]
            # print(message, end="", flush=True)
            # prev_text = data["message"]
        with open(f"test_gpt.json", "w", encoding="utf-8-sig") as f:
            json.dump(response, f)
        return self.parse_rewrited_data(response)

    def parse_rewrited_data(self, article: str):

        versions = {}
        current_version = None

        for line in article.split("\n"):
            if (
                "Professional and Friendly Tone" in line
                or "Version 1" in line
                or "First Version" in line
            ):
                current_version = "Professional and Friendly Tone"
                versions[current_version] = ""
            elif (
                "Conversational and Clear Tone" in line
                or "Version 2" in line
                or "Second Version" in line
            ):
                current_version = "Conversational and Clear Tone"
                versions[current_version] = ""
            elif (
                "Clear and Concise Tone" in line
                or "Version 3" in line
                or "Third Version" in line
            ):
                current_version = "Clear and Concise Tone"
                versions[current_version] = ""
            elif current_version:
                versions[current_version] += line + "\n"
        return versions

    def read_and_rewrite(self):
        filename = "rewrited_linkedin_post_of_Fabio Aversa, MBA 🧩"
        data = pd.read_csv(f"{filename}.csv").to_dict("records")
        counter = 0
        result = []
        start = datetime.now()
        try:
            logger.info("START SCRAPPING")
            for idx, d in enumerate(data):
                logger.info(idx)
                if d["is_scrapped"]:
                    continue
                content = d["content_of_the_post"]
                try:
                    rewrited_content = self.rewrite_content(content)
                except Exception as e:
                    logger.info(e)
                d["rewrited_content"] = rewrited_content
                d["professional_and_friendle"] = rewrited_content[
                    "Professional and Friendly Tone"
                ]
                d["conversational_and_clear"] = rewrited_content[
                    "Conversational and Clear Tone"
                ]
                d["clear and concise"] = rewrited_content["Clear and Concise Tone"]
                d["is_scrapped"] = True
                result.append(d)
                sleep(3)
                counter += 1
                logger.info(f"SCRAPPED {counter}")
                if counter == 10:
                    sleep(10)
                    counter = 0
                # if counter == 3:
                #     end = datetime.now()
                #     time = end - start
                #     time_int = int(time.total_seconds())
                #     sleep_time = 60 - time_int
                #     start = datetime.now()
                #     counter = 0
                #     logger.info(f"SLEEPING FOR {sleep_time} s")
                #     sleep(sleep_time)
        except:
            self._save_to_csv(data, "tmp_rewrited_" + filename)
        self._save_to_csv(data, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-linkedin_url")
    parser.add_argument("-yr", default=2)
    args = parser.parse_args()

    Scraper = LinkedInPostScraper()
    # Scraper.scrape_post(args.linkedin_url, args.yr)
    Scraper.read_and_rewrite()
