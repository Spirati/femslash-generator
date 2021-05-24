from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from typing import Dict, Union, Tuple
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
        polycule = int(request.args.get("polycule", 2))
        picks, ages = random_pairing(women, reference_year, polycule)
        return render_template("femslash.html", packed_women = tuple(zip(range(len(picks)), picks, ages)), reference_year=reference_year, polycule=polycule)

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


def valid_pairing(a: Name, b: Name, women: Dict[Name, Age], reference_year: int) -> bool:
    a_obj, b_obj = [{
        "name": name,
        "last_name": name.split(" ")[-1],
        "age": reference_year - women[name]
    } for name in (a,b)]

    related = a_obj["last_name"] == b_obj["last_name"]
    fey_blood = {a_obj["last_name"], b_obj["last_name"]} in ({"Fey", "Hawthorne"}, {"Iris", "Fey"}, {"Iris", "Hawthorne"}, {"Fey", "Bikini"})
    lower_a = a_obj["age"] < (7 + b_obj["age"]/2) # a is under the lower bound
    lower_b = b_obj["age"] < (7 + a_obj["age"]/2) # b is under the lower bound
    upper_a = a_obj["age"] > (2 * (b_obj["age"] - 7)) # a is over the upper bound
    upper_b = b_obj["age"] > (2 * (a_obj["age"] - 7)) # b is over the upper bound
    minor_gap_a = a_obj["age"] < 18 and b_obj["age"] > 18
    minor_gap_b = b_obj["age"] < 18 and a_obj["age"] > 18

    return not any((related, fey_blood, lower_a, lower_b, upper_a, upper_b, minor_gap_a, minor_gap_b)) 

def random_pairing(women: Dict[Name, Age], reference_year: int, polycule: int) -> Tuple[Tuple[Name], Tuple[Age]]:
    candidates = list(women.keys())

    candidates = list(filter(lambda candidate: reference_year - women[candidate] >= 16, candidates))

    candidate = random.choice(candidates)

    """
    eligible_bachelorettes = list(filter(
        lambda bachelorette:
            bachelorette != candidate and
            bachelorette.split(" ")[-1] != candidate.split(" ")[-1] and
            {bachelorette, candidate} != {"Dahlia Hawthorne", "Iris"} and
            {bachelorette.split(" ")[-1], candidate.split(" ")[-1]} not in ({"Fey", "Hawthorne"}, {"Iris", "Fey"}) and
            reference_year - women[bachelorette] > (7 + (reference_year - women[candidate])/2) and 
            reference_year - women[bachelorette] < (2 * (reference_year - women[candidate] - 7)) and
            reference_year - women[candidate] > (7 + (reference_year - women[bachelorette])/2) and 
            reference_year - women[candidate] < (2 * (reference_year - women[bachelorette] - 7)) and
            not ((reference_year - women[bachelorette] < 18 and reference_year - women[candidate] > 18) or (reference_year - women[bachelorette] > 18 and reference_year - women[candidate] < 18)),
        candidates
    ))
    """
    eligible_bachelorettes = list(filter(
        lambda bachelorette: valid_pairing(candidate, bachelorette, women, reference_year),
        candidates
    ))

    if candidate in eligible_bachelorettes: eligible_bachelorettes.remove(candidate)

    picks = set([candidate])

    if len(eligible_bachelorettes) == 0:
        return (candidate, "No one..."), (reference_year - women[candidate], "N/A")
    while len(picks) < polycule:
        try:
            choice = random.choice(eligible_bachelorettes)
        except:
            break
        picks.add(choice)
        if choice in eligible_bachelorettes: eligible_bachelorettes.remove(choice)
        eligible_bachelorettes = list(filter(
            lambda bachelorette: all([valid_pairing(c, bachelorette, women, reference_year) for c in tuple(picks)]),
            eligible_bachelorettes
        ))
    
    picks = tuple(picks)
    ages = tuple([reference_year - women[pick] for pick in picks])

    return picks, ages

    

