from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from typing import Dict, Union
import re
import random
from urllib import parse

import requests

def create_app():
    app = Flask(__name__)

    women = get_women()

    @app.route("/")
    def home_page():
        reference_year = int(request.args.get("reference_year", 2028))
        woman1, woman2, age1, age2 = random_pairing(women, reference_year)
        return render_template("femslash.html", woman1=woman1, woman2=woman2, reference_year=reference_year, age1=age1, age2=age2)

    @app.route("/women")
    def women_list():
        sorted_women = list(sorted(list(women.keys()), key=lambda key: women[key]))
        return render_template("character_list.html", women=women, women_list=sorted_women)

    return app

Name = str
Age = int

def get_women() -> Dict[Name, Age]:

    women: Dict[Name, Age] = dict()

    women_page = "https://aceattorney.fandom.com/wiki/Category:Female_characters"

    women_request = requests.get(women_page)

    women_parsed = BeautifulSoup(women_request.text, features="html5lib")
    
    all_letters = women_parsed("div", class_="category-page__members-wrapper")[2:] # exclude DGS and manga/stage characters
    all_links = []
    for section in all_letters:
        links = section("a", class_="category-page__member-link")
        all_links.extend(list(map(lambda link: "https://aceattorney.fandom.com" + link["href"], links)))

    for i, link in enumerate(all_links):
        result = are_you_a_real_human_woman_with_a_real_birthdate(link)
        if result:
            women[parse.unquote(link.split("/")[-1].replace("_"," "))] = result

        print("Processed {}/{} candidates ({:2.2f})".format(i+1, len(all_links), 100 * (i+1)/len(all_links)), end="\r")

    return women
    

WikiLink = str
def are_you_a_real_human_woman_with_a_real_birthdate(page: WikiLink) -> Union[bool, int]:
    woman_request = requests.get(page)

    if "\"Animals\"" in woman_request.text: return False

    woman_soup = BeautifulSoup(woman_request.text, features="html5lib")
    birthday_tag = woman_soup.find("div", {"data-source":"birthday"})

    if birthday_tag is None:
        return False
    
    birth_year = birthday_tag.find("div", class_="pi-data-value").text
    first_year = re.search(R"\d{4}", birth_year)
    if not first_year is None and int(first_year[0]) > 1910:
        return int(first_year[0])
    else:
        return False

def random_pairing(women: Dict[Name, Age], reference_year: int):
    candidates = list(women.keys())

    candidates = list(filter(lambda candidate: reference_year - women[candidate] >= 16, candidates))

    candidate = random.choice(candidates)

    eligible_bachelorettes = list(filter(
        lambda bachelorette:
            bachelorette != candidate and
            bachelorette.split(" ")[-1] != candidate.split(" ")[-1] and
            reference_year - women[bachelorette] > (7 + (reference_year - women[candidate])/2) and 
            reference_year - women[bachelorette] < (2 * (reference_year - women[candidate]) - 7) and
            reference_year - women[candidate] > (7 + (reference_year - women[bachelorette])/2) and 
            reference_year - women[candidate] < (2 * (reference_year - women[bachelorette]) - 7) and
            not ((reference_year - women[bachelorette] < 18 and reference_year - women[candidate] > 18) or (reference_year - women[bachelorette] > 18 and reference_year - women[candidate] < 18)),
        candidates
    ))

    if len(eligible_bachelorettes) == 0:
        return candidate, "No one...", reference_year - women[candidate], "N/A"
    choice = random.choice(eligible_bachelorettes)
    return candidate, choice, reference_year - women[candidate], reference_year - women[choice]

    

