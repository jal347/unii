import requests
import logging
import json
import pandas as pd

from biothings_client import get_client
from collections import defaultdict

GENE_CLIENT = get_client('gene')


logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)

def get_uniprot():
    url = "https://api.fda.gov/other/substance.json?search=codes.code_system:%22UNIPROT%22&"
    request = requests.get(url).json()
    doc = {}

    # TODO: raise runtimeerror
    if request["meta"]["results"]["total"] > 26000:
        logging.error("Exceeds limit to paginate see this page for more details: https://open.fda.gov/apis/paging/")
        return
    else:
        count = (request["meta"]["results"]["total"]-1)//1000

    for page in range(count+1):
        url = "https://api.fda.gov/other/substance.json?search=codes.code_system:%22UNIPROT%22&limit=1000&skip=" + str(page*1000)
        request = requests.get(url).json()
        for result in request["results"]:
            for code in result["codes"]:
                if code["code_system"] == "UNIPROT":
                    if code["code"] in doc.keys():
                        # print("the mapping is not 1-1: " + j["code"])
                        doc[code["code"]].append(result["unii"])
                    else:
                        doc[code["code"]] = [result["unii"]]
                else:
                    continue
    return doc


def query_uniprot(uniprot: list):
    """Use biothings_client.py to query uniprot codes and get back '_id' in mygene.info

    :param: uniprot: list of uniprot codes
    """
    res = GENE_CLIENT.querymany(uniprot, scopes='uniprot', fields='_id', returnall=True)
    new_res = defaultdict(list)
    for item in res['out']:
        if not "notfound" in item:
            new_res[item['query']].append(item['_id'])
    return [new_res, res]




# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    docs = get_uniprot()
    # print(docs["P01116"])
    ids = query_uniprot(list(docs.keys()))
    print(ids[0])
    recs = []
    for prot, unii in docs.items():
        gene_ids = ids[0][prot]
        for gene_id in gene_ids:
            rec = {
                "_id": gene_id,
                "unii": unii
            }
            recs.append(rec)

    data = pd.DataFrame.from_records(recs)
    data['mapping'] = data['unii'].str.len()
    mapping = data.groupby(["mapping"]).size().reset_index(name="count")
    print(mapping)


