import requests
import json


def getHTML(url:str)-> None:
    '''
    Makes request of the input url and returns response
    input: url
    '''
    session = requests.Session()
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit 537.36 (KHTML, like Gecko) Chrome"}
    try:
        re = session.get(url, headers=headers)
        return(re)

    except requests.exceptions.RequestException as e:  # This is the correct syntax
        raise SystemExit(e)

## The kind of query we want:
# ("Bioinformatics"[Journal:__jid9808944] AND 2018/01/01:2018/12/31[Date - Publication]) AND (2018/1/1:2018/12/31[pdat])

def build_journal_term(j_id, j_name):
    template = '"{j_name}"[Journal:__jid{j_id}]'
    return(template.format(j_name=j_name, j_id=j_id))

def build_pubdates_term(year):
    template='{year}/01/01:{year}/12/31[pdat]'
    return(template.format(year=year))

def esearch_journal_year(journal, journal_id, year):
    first_query_template='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={journal}&WebEnv=<webenv_string>&usehistory=y&retmode=json'
    # make first query for journal A
    url=first_query_template.format(journal=build_journal_term(journal_id, journal))
    print(url)
    first_re=getHTML(url)
    first=json.loads(first_re.text)
    # take <WebEnv>
    webenv=first['esearchresult']['webenv']
    querykey=first['esearchresult']['querykey']
    # Make intersection query based on year
    second_query_template = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={pub_dates}&query_key={querykey}&WebEnv={webenv}&usehistory=y&retmode=json'
    url=second_query_template.format(pub_dates=build_pubdates_term(year), querykey=querykey, webenv=webenv)
    intersect_re=getHTML(url)
    intersect=json.loads(intersect_re.text)
    # For each journal, find the papers we already have from agents and find them in the lists
    return(intersect)

# build a dict of journal_name => journal id from ftp://ftp.ncbi.nih.gov/pubmed/J_Medline.txt
with open('journals_ids.json', 'r') as ids_dict_in:
    jour_ids = json.load(ids_dict_in)

journals_top=['Bioinformatics', 
              'BMC Bioinformatics', 
              'Nucleic Acids Res', 
              'PLoS One', 
              'Nat Methods', 
              'Genome Biol', 
              'PLoS Comput Biol', 
              'Sci Rep', 
              'BMC Genomics',
              'J Cheminform']


# for the ten top pubs journals, fetch publications in the selected years
def fetch_papers_years(years, jour_ids, journals_top):
    journals_counts = {}
    for journal in journals_top:
        resps = {}
        journ_count = 0
        for year in years:
            count =  esearch_journal_year(journal, jour_ids[journal]['NlmId'], year)['esearchresult']['count']
            journ_count += int(count)
            resps[year] = count
        resps['total']=journ_count
        journals_counts[journal] = resps

    return(journals_counts)


journals_counts_five = fetch_papers_years([2015,2016,2017,2018,2019], jour_ids, journals_top)
journals_counts_two = fetch_papers_years([2018,2019], jour_ids, journals_top)



with open('journals_counts_five_10.json','w') as outjson:
    json.dump(journals_counts_five, outjson)


with open('journals_counts_two.json','w') as outjson:
    json.dump(journals_counts_two, outjson)