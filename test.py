from revChatGPT.V1 import Chatbot

chatbot = Chatbot(
    config={
        "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJqaG9yZHlAZGVsbWFuLmlvIiwiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsidXNlcl9pZCI6InVzZXItdExOV1Z1bDdtSmxkSUJlbVZvTHZ0ZGpKIn0sImlzcyI6Imh0dHBzOi8vYXV0aDAub3BlbmFpLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExMzIyMzk1NDM3NjUyNzk1MTEyMSIsImF1ZCI6WyJodHRwczovL2FwaS5vcGVuYWkuY29tL3YxIiwiaHR0cHM6Ly9vcGVuYWkub3BlbmFpLmF1dGgwYXBwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE2ODM2ODY1MDEsImV4cCI6MTY4NDg5NjEwMSwiYXpwIjoiVGRKSWNiZTE2V29USHROOTVueXl3aDVFNHlPbzZJdEciLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG1vZGVsLnJlYWQgbW9kZWwucmVxdWVzdCBvcmdhbml6YXRpb24ucmVhZCBvZmZsaW5lX2FjY2VzcyJ9.w3rY8B9iaERa3gccwl9Qn84Cx81CaUZj4u0WuoBPA82SNY2nqHqlcxnnHkNy1jMXdjh5dus8ymm8hc-MR65EGmjtGHaYwVR_qFEpEu6c81kDxcqfXFIkTiG9PSN12f2iskoA37KTY_qPDngIPlCT3AiOeuEtrhR1VyOxRbAkEDxxhzN5b8cYpXkXJ9wuSUPaz2havT0ILKUO-cNW2p1B2AdPUM-dJ65rZgRhG0KGIZy-r3K7zdbj4XD-E2MF4SYy09YTe8nqSz9TJc0YuyRLonGakA9wQ16iatL_RjPCmqdTYF965LzLN4uwivy2nnw15hBFk7cVD5OdSUZJWwPz_g",
        "model": "text-davinci-002-render-sha",
    }
)
print("Chatbot: ")
prompt = """act as mssql server developer wrap query1 with select statement from list1 with rules:
        1. selecting rename value if rename exists
        2. if rename doesnt exists, selecting the name values
query1 = WITH ALLDATA AS (\nSelect Distinct   \na.LetterRequestID,\nA.TERM,\na.LetterTypeID,\nb.LetterTypeDesc,     \nc.LetterLanguage,\nrequestor.BinusianID,    \ncoalesce(u.userID ,requestor.BinusianID,'') AS NIM , f.FullName,\nSelectedResult = case when l.LetterTypeResultID = 1 then 'DIGITAL' else 'SIGN' end,\nRequestDate = Convert(DATE, a.RequestDate),     \nProcessDate = Coalesce(Convert(varchar(12), a.ProcessDate, 0), ' '),     \nFinishDate = Coalesce(Convert(varchar(12), l.FinishDate, 0), ' '),    \nPickupDate = Coalesce(Convert(varchar(12), l.PickupDate, 0), ' '),    \nDownloadDate = Coalesce(Convert(varchar(12), l.DownloadDate, 0), ' '),   \nProcessBy = CASE WHEN h.FullName Is NULL then 'Binus Online Staff' Else UPPER(h.FullName) End,\na.LetterStatusID, e.LetterStatusDescription,\nProcessTimeSLA= CASE WHEN EXISTS(SELECT * FROM TrPsHolidayDateServiceOnline WHERE HOLIDAY>=a.RequestDate AND HOLIDAY<=l.FinishDate)\nTHEN DATEDIFF(day,a.RequestDate,l.FinishDate)-(SELECT COUNT(*) FROM TrPsHolidayDateServiceOnline WHERE HOLIDAY>=a.RequestDate AND HOLIDAY<=l.FinishDate)\nELSE DATEDIFF(day,a.RequestDate,l.FinishDate) END\nFrom TrLetterRequestServiceOnline a with (nolock)    \nLeft join DimLetterTypeServiceOnline b with (nolock) on a.LetterTypeID = b.LetterTypeID    \nLeft join DimLetterTypeLanguageServiceOnline c with (nolock) on a.LetterTypeID = c.LetterTypeID and a.LetterLanguage = c.LetterLanguage    \nLEFT join TrLetterServiceOnline l on a.LetterRequestID = l.LetterRequestID\nLeft join\n(\n\tSelect *\n\tFrom TrLetterRequestorServiceOnline with (nolock)\n\tWhere BinusianID = userInput\n) d on a.LetterRequestID = d.LetterRequestID   \nLeft join TrLetterRequestorServiceOnline requestor with(nolock) on a.letterrequestID  = requestor.LetterRequestID\nLeft join DimLetterRequestStatusServiceOnline e with (nolock) on a.LetterStatusID = e.LetterStatusID     \nLeft join DimBinusianprofileServiceOnline f on ltrim(rtrim(requestor.BinusianID)) = ltrim(rtrim(f.BinusianID))    \nLeft join DimBinusianprofileServiceOnline h on a.ProcessBy = h.BinusianID\nleft join TrMappingUserRoleServiceOnline u on u.BinusianID = requestor.BinusianID \n)\nSELECT \nA.LetterRequestID,\nA.TERM,\nA.LetterTypeID,\nA.LetterTypeDesc,     \nA.LetterLanguage,\nA.BinusianID,    \nA.NIM, \nA.FullName,\nA.SelectedResult,\nA.RequestDate,     \nA.ProcessDate,     \nA.FinishDate,    \nA.PickupDate,    \nA.DownloadDate,   \nA.ProcessBy,\nA.LetterStatusID, A.LetterStatusDescription,\nCASE WHEN A.ProcessTimeSLA IS NULL THEN '' ELSE A.ProcessTimeSLA End As 'ProcessTimeSLA'\n, CASE WHEN A.LETTERSTATUSID = '4' AND A.PROCESSTIMESLA > C.SLA THEN 'Overdue' \nWHEN A.LETTERSTATUSID <> '4' THEN A.LETTERSTATUSDescription ELSE 'On Time' END AS 'SLA STATUS'\n, CASE WHEN A.DownloadDate ='' THEN 'Not Downloaded' ELSE 'Already Downloaded' END AS DOWNLOADSTATUS\n, concat(letterrequestid, BinusianID) \"LetterIdAll\"\n, Getdate() \"QueryDateTime\"\nFROM ALLDATA A\nJOIN DimPSNPersoncarTBL B ON B.ACAD_CAREER IN ('OS1') AND A.BinusianID = B.EMPLID AND A.NIM = B.EXTERNAL_SYSTEM_ID\nLEFT JOIN DimLetterTypeServiceOnline C ON A.LETTERTYPEID = C.LETTERTYPEID

list1 = [
                                    {
                                        "name": "LetterRequestID",
                                        "rename": null
                                    },
                                    {
                                        "name": "TERM",
                                        "rename": "Term"
                                    },
                                    {
                                        "name": "LetterTypeID",
                                        "rename": null
                                    },
                                    {
                                        "name": "LetterTypeDesc",
                                        "rename": "LetterTypeDescription"
                                    },
                                    {
                                        "name": "LetterLanguage",
                                        "rename": null
                                    },
                                    {
                                        "name": "BinusianID",
                                        "rename": null
                                    },
                                    {
                                        "name": "NIM",
                                        "rename": "ExternalSystemID"
                                    },
                                    {
                                        "name": "FullName",
                                        "rename": null
                                    },
                                    {
                                        "name": "SelectedResult",
                                        "rename": null
                                    },
                                    {
                                        "name": "RequestDate",
                                        "rename": null
                                    },
                                    {
                                        "name": "ProcessDate",
                                        "rename": null
                                    },
                                    {
                                        "name": "FinishDate",
                                        "rename": null
                                    },
                                    {
                                        "name": "PickupDate",
                                        "rename": null
                                    },
                                    {
                                        "name": "DownloadDate",
                                        "rename": null
                                    },
                                    {
                                        "name": "ProcessBy",
                                        "rename": null
                                    },
                                    {
                                        "name": "LetterStatusID",
                                        "rename": null
                                    },
                                    {
                                        "name": "LetterStatusDescription",
                                        "rename": null
                                    },
                                    {
                                        "name": "ProcessTimeSLA",
                                        "rename": null
                                    },
                                    {
                                        "name": "SLA STATUS",
                                        "rename": "SlaStatus"
                                    },
                                    {
                                        "name": "DOWNLOADSTATUS",
                                        "rename": "DownloadStatus"
                                    },
                                    {
                                        "name": "LetterIdAll",
                                        "rename": "LetterIDAll"
                                    },
                                    {
                                        "name": "QueryDateTime",
                                        "rename": null
                                    }
                                ]

only return to me the complete all query that compatible with microsoft sql server in an optimized query"""
prev_text = ""
for data in chatbot.ask(prompt):
    message = data["message"][len(prev_text) :]
    print(message, end="", flush=True)
    prev_text = data["message"]
for data in chatbot.ask("continue"):
    message = data["message"][len(prev_text) :]
    print(message, end="", flush=True)
    prev_text = data["message"]
print(prev_text)
