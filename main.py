### IMPORTS ##################

from flask import Flask, jsonify
import requests
from lxml import html


### CONSTANTS ################

LINKEDIN_URL_PREFIX="https://www.linkedin.com/in"
LINKEDIN_SEARCH_URL_PREFIX="https://www.linkedin.com/pub/dir"

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/21.0'
}

data2xpath = {
    "Name" : '//*[@id="name"]',
    "Title" : '//*[@id="topcard"]/div[1]/div[2]/div/p',
    #//*[@id="topcard"]/div[1]/div[2]/div/p
    #//*[@id="headline"]/p
    "Current Positions" : '//*[@id="topcard"]/div[1]/div[2]/div/table/tbody/tr[1]/td/ol',
    "Summary" : '//*[@id="summary-item-view"]/div/p',
    #//*[@id="summary"]/div/p
    "Skills" : ('//*[@id="skills"]/ul', ['skill','skill extra'])
}

### CODE #####################

app = Flask(__name__)


@app.route('/url/<path:url>')
def get_data_from_url(url):
    result = {}
    response = requests.get(LINKEDIN_URL_PREFIX + "/" + url, headers=headers)
    tree = html.fromstring(response.content)
    for dataName, xpath in data2xpath.iteritems():
        
        if type(xpath) != tuple:
            data = tree.xpath(xpath)
            try:
                result[dataName] = str(data[0].text_content())
            except:
                result[dataName] = "No Data"
        else:
            data = tree.xpath(xpath[0])
            result[dataName] = str(", ".join(map(lambda x: x.text_content(), filter(lambda x: x.get('class') in xpath[1], data[0].getchildren()))))
      
    return jsonify(**result)

@app.route('/search/first_name=<first_name>&last_name=<last_name>')
def search_for_people(first_name, last_name):
    result = {}
    response = requests.get(LINKEDIN_SEARCH_URL_PREFIX + "/?first=" + first_name + "&last=" + last_name, headers=headers)
    tree = html.fromstring(response.content)
    i = 1
    while True:
        try:
            element = tree.xpath('//*[@id="wrapper"]/div[2]/div[1]/ul/li['+str(i)+']/div/div/h3/a')
            result[str(element[0].text_content())] = str(element[0].get('href'))
        except Exception, e:
            break
        i += 1
    return jsonify(**result)


@app.route('/skill_count/first_name=<first_name>&last_name=<last_name>')
def search_for_people_skill_count(first_name, last_name):
    result = {}
    response = requests.get(LINKEDIN_SEARCH_URL_PREFIX + "/?first=" + first_name + "&last=" + last_name, headers=headers)
    tree = html.fromstring(response.content)
    i = 1
    while True:
        try:
            element = tree.xpath('//*[@id="wrapper"]/div[2]/div[1]/ul/li['+str(i)+']/div/div/h3/a')
            specific_person_response = requests.get(str(element[0].get('href')), headers=headers)
            specific_person_tree = html.fromstring(specific_person_response.content)
            specific_person_skills = specific_person_tree.xpath(data2xpath['Skills'][0])
            result[str(element[0].text_content())] = str(len(filter(lambda x: x.get('class') in data2xpath['Skills'][1], specific_person_skills[0].getchildren())) if len(specific_person_skills) > 0 else 0)
        except Exception, e:
            break
        i += 1
    return jsonify(**result)

### MAIN ######################

if __name__ == '__main__':
    app.run()