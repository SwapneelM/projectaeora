from collections import defaultdict
import html2text
from textblob import TextBlob
import requests
import bs4
import os


def get_stopwords():
    #source=http://xpo6.com/list-of-english-stop-words/
    filepath = os.path.dirname(__file__) + '/stopwords.txt' 
    stopwords = list() 
    with open(filepath) as fp:  
        line = fp.readline()
        while line:
            stopwords.append(line.strip())
            line = fp.readline()
    return stopwords

def get_keywords(article):
    stopwords = get_stopwords()
    words = article.words
    non_stopwords = list()
    for word in words:
        if word.lower() not in stopwords:
            non_stopwords.append(word.lower())
    words_sorted_by_frequency = sorted(non_stopwords,key=non_stopwords.count,reverse=True)
    keywords = set()
    for word in words_sorted_by_frequency:
        if len(keywords)<3:
            keywords.add(word.title())
        else:
            break
    return list(keywords)

def big_movers_card(top5, risers=True):
    """
    Returns a dictionary containing the layout of the big movers card tables.

    Keyword arguments:
    top5 - a list of tuples containing data about the top 5 companies
    risers - specified whether the list contains the risers (True) or fallers (False)
    """
    big_movers = defaultdict()

    # Build phrase for the voice output.
    category = 'risers' if risers else 'fallers'
    speech = 'The top 5 ' + category + ' are '
    companies = []

    for i in range(len(top5)):
        row = defaultdict()
        row['name'] = top5[i][0]
        row['price'] = top5[i][1]
        row['percentage_change'] = top5[i][2]

        speech += row['name']
        if i < len(top5) - 2:
            speech += ', '
        else:
            if i == len(top5) - 1:
                speech += '.'
            else:
                speech += ' and '

        companies.append(row)

    big_movers['speech'] = speech

    # Build elements for the card visualisation
    card = defaultdict()
    card['title'] = 'Top ' + category.title()
    card['companies'] = companies

    big_movers['text'] = card
    big_movers['type'] = 'top'

    return big_movers

def get_analysis(url, characters):
    response = requests.get(url)
    if (response.status_code == 200):
        soup = bs4.BeautifulSoup(response.text, 'lxml') #, 'lxml')
        article = html2text.html2text(soup.find('html').get_text()).split("/**/")[1]
        summary = article.replace("\n", " ")[:characters]+"..." 
        blob = TextBlob(article)
        keywords = get_keywords(blob)
        if blob.sentiment.polarity > 0:
            return summary, "positive", keywords 
        elif blob.sentiment.polarity == 0:
            return summary, "neutral", keywords
        else:
            return summary, "negative", keywords        
    return "No summary available", "none", set()

def news_reply(lse_list, yahoo_list):

    lse_news = []
    for el in lse_list:
        row = {}
        row["date"] = el.date
        row["headline"] = el.headline
        row["url"] = el.url
        row["source"] = el.source
        row["impact"] = el.impact
        row["summary"], row["sentiment"],row["keywords"] = get_analysis(el.url, 250)
        lse_news.append(row)

    yahoo_news = []
    for el in yahoo_list:
        row = {}
        row["date"] = el.date
        row["headline"] = el.headline
        row["url"] = el.url
        row["source"] = el.source
        row["impact"] = el.impact
        row["summary"] = el.description
        yahoo_news.append(row)

    news = {"LSE": lse_news, "YAHOO": yahoo_news}
    overall_dict = {
        "speech": "Here are some news articles that I've found!",
        "type": "news",
        "text": news
    }

    return overall_dict


def get_company_reply(company, attribute):
    reply = defaultdict()

    try:
        value = getattr(company.stock, attribute)
    except AttributeError:
        value = getattr(company, attribute)

    #related_attribute determines what related data will appear to complement the requested data
    related_attribute = {"bid": "offer", "offer": "bid", "sector": "sub_sector"
    , "sub_sector": "sector", "high": "low", "low" : "high", "diff": "per_diff"
    , "per_diff": "diff",  "last_close_value": "last_close_date"
    ,"last_close_date": "last_close_value", "revenue": "market_cap"
    ,"market_cap": "volume", "volume" : "price", "price": "per_diff"}

    #to_english determines the english word that will be substituted for the attribute name
    to_english = {"bid": "bid", "offer": "offer", "sector": "sector", "sub_sector": "sub-sector",
    "high": "high", "low": "low", "diff": "change", "per_diff": "percentage change",
    "last_close_value": "last close", "last_close_date": "last close date", "revenue": "revenue",
    "market_cap": "market cap", "volume": "volume", "price": "price"}
    secondary_attribute = related_attribute[attribute]

    try:
        secondary_value = getattr(company.stock, secondary_attribute)
    except AttributeError:
        secondary_value = getattr(company, secondary_attribute)

    card = {'name' : company.name,'code': company.code,'date': company.date,'primary': value,
    'secondary': secondary_value,'primary_type': attribute, 'secondary_type': secondary_attribute}

    reply['text'] = card
    reply['type'] = 'company'
    reply['speech'] = "The " + to_english[attribute] + " of " + company.name + " is " + value #The text to be spoken by the agent

    return reply

def sector_reply(sector, sector_attribute):
    data = getattr(sector, sector_attribute)
    if (sector_attribute == "highest_price" or sector_attribute == "lowest_price"):
        data = getattr(sector, sector_attribute)
        sector_name = sector.name
        speech = "{} has the {} {} in {}: {}".format(data.name, sector_attribute.split('_',1)[0], sector_attribute.split('_', 1)[1], sector_name, getattr(data.stock, sector_attribute.split('_', 1)[1]))
        response = get_company_reply(data, "price")
        response['speech'] = speech
        return response
    elif sector_attribute == "rising" or sector_attribute == "falling":
        number_of_companies_in_sector = len(sector.companies)
        number_of_companies_moving_in_requested_direction = len(data)
        speech = ""
        if number_of_companies_moving_in_requested_direction == 0:
            speech = "No "+sector.name+" companies are "+sector_attribute+". "
            if sector_attribute == "rising":
                sector_attribute = "falling"
            else:
                sector_attribute = "rising"
            data = getattr(sector, sector_attribute)
        speech += "The following "+sector.name+" companies are "+sector_attribute+". "
        companies = []
        for i in range(len(data)):
            row = defaultdict()
            row['name'] = data[i].name
            row['price'] = data[i].stock.price
            row['percentage_change'] = data[i].stock.per_diff
            speech += row['name']
            if i < len(data) - 2:
                speech += ', '
            else:
                if i == len(data) - 1:
                    speech += '.'
                else:
                    speech += ' and '
            companies.append(row)
        movers = defaultdict()
        movers['speech'] = speech
        # Build elements for the card visualisation
        card = defaultdict()
        card['title'] = str(len(data))+'/'+str(number_of_companies_in_sector)+' '+sector.name+' are '+sector_attribute
        card['companies'] = companies
        movers['text'] = card
        movers['type'] = 'top'
        return movers

def revenue_reply(company):
    response = {}

    card = {}
    card['title'] = "Revenue Data for " + company.name
    card['revenue_data'] = list()

    response['speech'] = "Here is the revenue data for " + company.name
    response['type'] = "revenue"
    response['text'] = card

    for i in range(len(company.revenue)):
        row = {}
        row['date'] = company.revenue[i][0]
        row['revenue'] = company.revenue[i][1]
        card['revenue_data'].append(row)

    return response
