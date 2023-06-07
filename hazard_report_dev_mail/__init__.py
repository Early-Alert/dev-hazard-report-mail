import logging
import requests
import urllib.request
from datetime import datetime
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import os 


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Function Hit")
    req_body = req.get_json()
    logging.info('Python HTTP trigger function processed a request.')
    response = send_hazard_report(req_body)
    logging.info(f"****** {response} ******")
    return func.HttpResponse(
            "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
            status_code=200
            )

def send_hazard_report(request):
    # request_d = json.loads(request.data)
    logging.info("Triggered Datetime --> {}".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
    logging.info("Request contain this body {}".format(request))
    subject = request.get('personalizations')[0].get('dynamic_template_data').get('subject')
    
    from_email = request.get('from').get('email')
    bcc = request.get('personalizations')[0].get('bcc')[0].get('email')
    logo_url = request.get('personalizations')[0].get('dynamic_template_data').get('logo_url')
    blob_url = request.get('personalizations')[0].get('dynamic_template_data').get('blob_url')
    length = len(request.get('personalizations')[0].get('to'))
    to_list = []
    for i in range(length):
        to_email = request.get('personalizations')[0].get('to')[i].get('email')
        to_list.append(to_email)    
    length_bcc = len(request.get('personalizations')[0].get('bcc'))
    bcc_list = []
    for i in range(length_bcc):
        bcc_email = request.get('personalizations')[0].get('bcc')[i].get('email')
        bcc_list.append(bcc_email)

    fp = urllib.request.urlopen("{}".format(blob_url))
    mybytes = fp.read()
    mystr = mybytes.decode("utf8")

    tags_list = []
    if request.get('client'):
        tags_list.append(request.get('client'))
    if request.get('cid'):
        tags_list.append(request.get('cid'))
    if request.get('report_type'):
        tags_list.append(request.get('report_type'))
    logging.info("In BCC {}".format(bcc_list))
    logging.info("Sending email to these clients {}".format(to_list))



    list_of_files = []
    if request.get('attachments') != []:
        for each_file in range(len(request.get('attachments'))):
            filename = str(request.get('attachments')[each_file].get('url')).replace("https://earlyalert.blob.core.windows.net/rt-images/","")
            blob_service_client = BlobServiceClient(account_url="https://earlyalert.blob.core.windows.net/", credential= "aAZ2y630FObaCAdehtruxMGtjxH/p9CK1x4NlYrfDQDu75BOveB+u1ObTUpf61ena6wQdNrys8mzwqh0qIu1BA==")
            blob_client = blob_service_client.get_blob_client(container="rt-images", blob=filename)
            with open(file=os.path.join('/tmp', filename), mode="wb") as sample_blob:
                download_stream = blob_client.download_blob()
                sample_blob.write(download_stream.readall())
                current_filename = os.path.join('/tmp', filename)
                renamed_file = os.rename(current_filename, os.path.join("/tmp", request.get('attachments')[each_file].get('name')))
                new_file = os.path.join("/tmp", request.get('attachments')[each_file].get('name'))
                list_of_files.append(new_file)

        logging.info(f"List of files {list_of_files}")
        send_email = requests.post("https://api.mailgun.net/v3/earlyalert.com/messages",
            auth=("api", "key-abc3ac7030c2113b91c27b6733ebe510"),
                files = [("attachment", (f, open(f, "rb").read())) for f in list_of_files],
                data={"from": from_email,
                    "to": to_list,
                    "bcc" : bcc_list,
                    "subject": subject,
                    "html": mystr,
                    "o:tag": tags_list
                    })
    else:
        send_email = requests.post("https://api.mailgun.net/v3/earlyalert.com/messages",
            auth=("api", "key-abc3ac7030c2113b91c27b6733ebe510"),
                data={"from": from_email,
                    "to": to_list,
                    "bcc" : bcc_list,
                    "subject": subject,
                    "html": mystr,
                    "o:tag": tags_list
                    })
    return f'Function App Run at {datetime.now().strftime("%d/%m/%Y %H:%M:%S")} with status --- {send_email.text} ---'



"""
    if request.get('attachments') != []:
        logging.info("File we get in bytes --> {}".format(request.get('attachments')[0].get('url')))
        filename = str(request.get('attachments')[0].get('url')).replace("https://earlyalert.blob.core.windows.net/rt-images/","")
        blob_service_client = BlobServiceClient(account_url="https://earlyalert.blob.core.windows.net/", credential= "aAZ2y630FObaCAdehtruxMGtjxH/p9CK1x4NlYrfDQDu75BOveB+u1ObTUpf61ena6wQdNrys8mzwqh0qIu1BA==")
        blob_client = blob_service_client.get_blob_client(container="rt-images", blob=filename)
        with open(file=os.path.join('/tmp', filename), mode="wb") as sample_blob:
            download_stream = blob_client.download_blob()
            sample_blob.write(download_stream.readall())
            current_filename = os.path.join('/tmp', filename)
            renamed_file = os.rename(current_filename, os.path.join("/tmp", request.get('attachments')[0].get('name')))
            new_file = os.path.join("/tmp", request.get('attachments')[0].get('name'))

        send_email = requests.post("https://api.mailgun.net/v3/earlyalert.com/messages",
            auth=("api", "key-abc3ac7030c2113b91c27b6733ebe510"),
                files = [("attachment", (f"/tmp/{filename}", open(f"/tmp/{filename}", "rb").read()))],
                data={"from": from_email,
                    "to": to_list,
                    "bcc" : bcc_list,
                    "subject": subject,
                    "html": mystr,
                    "o:tag": tags_list
                    })

"""