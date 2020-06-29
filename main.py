import json
import public_config as c
import logging
import argparse
from tinydb import TinyDB, Query


from juriscraper.pacer import (
    DocketReport,
    PacerSession,
    PossibleCaseNumberApi,
    FreeOpinionReport,
)

logging.basicConfig(level=logging.DEBUG)

district_dict = {
    "00": "med",
    "01": "mad",
    "02": "nhd",
    "03": "rid",
    "05": "ctd",
    "10": "vtd",
}


class PlymouthState(object):
    logging.info("Initializing Plymouth State object")

    s = PacerSession(username=c.PACER_USERNAME, password=c.PACER_PASSWORD)
    results = []

    def docket_to_dn(self, case):
        return "".join(
            [case["OFFICE"], ":", case["DOCKET"][:2], "-cv-", case["DOCKET"][3:]]
        )

    def write_to_file(self):
        with open("adhoc/pacer_data.json", "w") as write_file:
            json.dump(self.results, write_file, indent=4)

    def get_pacer_court_ids(self):
        q = Query()
        db = TinyDB("db/master.json")
        fjc_table = db.table("fjc")
        for row in fjc_table.search((q.PACER_CASE_ID == "")):
            report = PossibleCaseNumberApi(row["COURT"], self.s)
            report.query(row["DOCKET_NO"])
            data = report.data(office_number=row["OFFICE"], docket_number_letters="cv")
            fjc_table.update(
                {"PACER_CASE_ID": data["pacer_case_id"], "TITLE": data["title"]},
                doc_ids=[row.doc_id],
            )

    def get_docket_json(self):
        s = PacerSession(username=c.PACER_USERNAME, password=c.PACER_PASSWORD)
        q = Query()
        db = TinyDB("db/master.json")
        fjc_table = db.table("fjc")
        print "docket"
        for row in fjc_table.search((q.JSON == "False")):
            print "ROW", row
            # print row['COURT'], row['PACER_CASE_ID']
            # break
            rep = DocketReport(row["COURT"], s)
            rep.query(
                row["PACER_CASE_ID"],
                show_parties_and_counsel=True,
                show_terminated_parties=True,
                show_list_of_member_cases=True,
                include_pdf_headers=True,
                show_multiple_docs=False,
            )
            with open(
                "downloads/json/pacer_docket_%s.json" % row["PACER_CASE_ID"], "w"
            ) as write_file:
                json.dump(rep.data, write_file, indent=4, sort_keys=True, default=str)
            with open(
                "downloads/html/pacer_docket_%s.html" % row["PACER_CASE_ID"], "w"
            ) as file:
                file.write(rep.response.text)

            fjc_table.update(
                {
                    "JSON": "True",
                    "pacer_doc_id": rep.data["docket_entries"][0]["pacer_doc_id"],
                },
                doc_ids=[row.doc_id],
            )
            break
        print "end"

    def download_pdfs(self):
        s = PacerSession(username=c.PACER_USERNAME, password=c.PACER_PASSWORD)
        q = Query()
        db = TinyDB("db/master.json")
        fjc_table = db.table("fjc")
        for row in fjc_table.search((q.PDF == "False") & (q.pacer_doc_id).exists()):
            logging.info(
                "Collecting PDF #%s, in %s" % (row["PACER_CASE_ID"], row["TITLE"])
            )
            report = FreeOpinionReport(row["COURT"], s)
            r = report.download_pdf(row["PACER_CASE_ID"], row["pacer_doc_id"])
            with open(
                "downloads/pdf/pacer_complaint_%s.pdf" % row["PACER_CASE_ID"], "w"
            ) as file:
                file.write(r.content)

            fjc_table.update(
                {"PDF": "True"}, doc_ids=[row.doc_id],
            )
            logging.info(
                "Collected PDF #%s, in %s" % (row["PACER_CASE_ID"], row["TITLE"])
            )


def get_pacer_ids():
    logging.info("Begin collecting PACER CASE IDS")

    p = PlymouthState()
    p.get_pacer_court_ids()


def download_json_html():
    logging.info("Begin collecting Dockets")

    p = PlymouthState()
    p.get_docket_json()


def get_pdfs():
    logging.info("Begin collecting PDFS")

    p = PlymouthState()
    p.download_pdfs()


def zip_files():
    import shutil

    shutil.make_archive("downloads/zip/html_files", "zip", "downloads/html/")
    shutil.make_archive("downloads/zip/pdf_files", "zip", "downloads/pdf/")
    shutil.make_archive("downloads/zip/json_files", "zip", "downloads/json/")

def testing():
    print "Test"

    q = Query()
    db = TinyDB("db/master.json")
    fjc_table = db.table("fjc")
    for row in fjc_table:
        print row
    # x = fjc_table.search((q.YEAR == "2012"))
    # print len(x)
    # for row in fjc_table.search((q.PDF == "False") & (~ (q.YEAR == "2017"))):
    #     print row['YEAR'], row


class Command(object):
    help = "Collect cases for Plymouth State"

    VALID_ACTIONS = {
        "testing": testing,
        "get-pacer-ids": get_pacer_ids,
        "get-dockets": download_json_html,
        "get-pdfs": get_pdfs,
        "zip-files": zip_files,
    }

    parser = argparse.ArgumentParser(description="Process Plymouth State")
    parser.add_argument("-a", "--action", help="Must choose an action", required=True)
    args = vars(parser.parse_args())
    VALID_ACTIONS[args["action"]]()
