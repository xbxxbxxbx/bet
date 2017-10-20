from __future__ import division
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from collections import defaultdict, Counter
from bson.json_util import dumps
from pymongo import MongoClient
import numpy as np
import datetime
import time
import json
import sys




def setup_page():
    print "%20s" % "Page setup:", "%20s" % "Started"

    # open date filter for RESULTS
    results_header = driver.find_element_by_id("league-summary-results")
    filter = results_header.find_elements_by_class_name("select")[0]
    filter.click()
    time.sleep(3)

    # select longest range, 6 months
    last_option = filter.find_element_by_class_name("last")
    last_option.click()
    time.sleep(3)

    print "%20s" % "Page setup:", "%20s" % "Finished\n"


def get_next_matches():
    print "%20s" % "Getting matches:", "%20s" % "Started"

    all_tables = driver.find_elements_by_class_name("table-main")
    next_matches_table = all_tables[0]

    for row in next_matches_table.find_elements_by_xpath(".//tr"):

        if len(row.find_elements_by_tag_name("td")) != 9:              # 0 is heading, 10 is a live game
            continue

        match_data = [str(td.text) for td in row.find_elements_by_tag_name("td")]  # (EMPTY), Home - Away, ...


        (home_team, away_team) = match_data[1].split(" - ")
        match = [ (home_team, away_team),  match_data[5:] ]
        next_matches.append(match)

    print "%20s" % "Getting matches:", "%20s" % "Finished"
    print "\n"


def get_rankings():
    print "%20s" % "Getting rankings:", "%20s" % "Started"

    ranking_types = [
        ('overall', 'stats-menu-overall', 'table-type-1'),
        ('home', 'stats-menu-home', 'table-type-2'),
        ('away', 'stats-menu-away', 'table-type-3')
    ]

    for ranking_type, tab_name, table_name in ranking_types:
        headers = driver.find_element_by_id('glib-stats-submenu-table')
        tab = headers.find_element_by_class_name(tab_name)
        tab.click()
        time.sleep(3)

        team_rankings = []

        rankings_table = driver.find_element_by_id(table_name)

        for row in rankings_table.find_elements_by_xpath(".//tr"):
            if len(row.find_elements_by_tag_name("td")) == 0:
                continue

            row_data = [str(td.text) for td in row.find_elements_by_tag_name("td")]  # (EMPTY), Home - Away, ...
            team_name = row_data[1]
            team_rankings.append(team_name)

            if ranking_type == 'overall':
                team_rankings_overall.append(team_name)

        team_rankings_dict[ranking_type] = team_rankings

    print "%20s" % "Getting rankings:", "%20s" % "Finished"
    print "\n"


def get_form():
    print "%20s" % "Getting form:", "%20s" % "Started"

    driver.find_element_by_class_name('stats-menu-form').click()
    time.sleep(5)

    # Overall
    form_types = [
        ('overall','stats-menu-overall', 'stats-menu-5-', 'table-type-5-'),
        ('home','stats-menu-home', 'stats-menu-8-','table-type-8-'),
        ('away','stats-menu-away', 'stats-menu-9-' ,'table-type-9-')
    ]


    for form_type, tab_name, sub_tab_name, table_name in form_types:
        # glib-stats-submenu-form -> glib-stats-submenu-form-away -> stats-menu-9-30 -> table-type-9-30

        headers = driver.find_element_by_id('glib-stats-submenu-form')
        tab = headers.find_element_by_class_name(tab_name)  # overall, home, away
        tab.click()
        time.sleep(3)

        sub_tab_menu = driver.find_element_by_id("glib-stats-submenu-form-" + form_type)
        li_list = sub_tab_menu.find_elements_by_tag_name("li")  # 5, 10, 15

        game_count = str(len(li_list) * 5)

        driver.find_element_by_id(sub_tab_name + game_count).click()
        time.sleep(3)

        overall_form_table = driver.find_element_by_id(table_name + game_count)
        tr_list = overall_form_table.find_elements_by_xpath(".//tr")

        for row in tr_list:
            if len(row.find_elements_by_tag_name("td")) == 0:
                continue


            form_data = [str(td.text) for td in row.find_elements_by_tag_name("td")]         # Rank, Name, MP, Wins, Draws, Losses, Goals, Match Points, Last 5 (EMPTY)

            form = ''
            last_5 = row.find_elements_by_class_name("matches-5")[0]
            games = last_5.find_elements_by_class_name("form-bg")


            for game in games:
                if "form-s" in game.get_attribute("class"):  # skip [?] box
                    continue

                win = "form-w" in game.get_attribute("class")
                loss = "form-l" in game.get_attribute("class")
                draw = "form-d" in game.get_attribute("class")

                if win:
                    form += '1'
                elif loss:
                    form += '0'
                else:
                    form += '-'

            form_data.pop(0)                         # remove rank
            team_name = form_data.pop(0)             # remove team name
            form_data.pop(0)                         # remove matches played
            # form_data[-1] = form                     # swap '' for 01101

            (goals_scored, goals_allowed) = form_data[3].split(":")

            # new form_data structure
            # wins, draws, losses, goals, match points, form (EMPTY)

            form_dict[form_type][team_name] = {
                'wins': form_data[0],
                'draws': form_data[1],
                'losses': form_data[2],
                'goals_scored': goals_scored,
                'goals_allowed': goals_allowed,
                'form': form
            }

    print "%20s" % "Getting form:", "%20s" % "Finished\n"


def get_over_under():
    print "%20s" % "Getting O/U:", "%20s" % "Started"

    driver.find_element_by_xpath('//a[contains(text(),"Over/Under")]').click()
    time.sleep(5)

    table_types = [
        ('overall','stats-menu-overall', 'table-type-6-2.5'),
        ('home','stats-menu-home', 'table-type-17-2.5'),
        ('away','stats-menu-away', 'table-type-18-2.5')
    ]


    for table_type, tab_name, table_name in table_types:

        headers = driver.find_element_by_id('glib-stats-submenu-over_under')
        tab = headers.find_element_by_class_name(tab_name)
        tab.click()
        time.sleep(3)


        over_under_table = driver.find_element_by_id(table_name)

        tr_list = over_under_table.find_elements_by_xpath(".//tr")

        for index, row in enumerate(tr_list):
            if len(row.find_elements_by_tag_name("td")) == 0:
                continue


            over_under_data = [str(td.text) for td in row.find_elements_by_tag_name("td")]         # Rank, Name, MP, Over, Under, Goals, Goals per Match, Last 5 (EMPTY)

            form = ''
            last_5 = row.find_elements_by_class_name("matches-5")[0]
            games = last_5.find_elements_by_class_name("form-ou")

            for game in games:
                over = "form-over" in game.get_attribute("class")
                if over:
                    form += '1'
                else:
                    form += '0'


            team_name = over_under_data[1]
            (goals_scored, goals_allowed) = over_under_data[5].split(":")

            over_under_dict[table_type][team_name] = {
                'over': over_under_data[3],
                'under': over_under_data[4],
                'goals_scored': goals_scored,
                'goals_allowed': goals_allowed,
                'goals_per_match': over_under_data[6],
                'form': form
            }

    print "%20s" % "Getting O/U:", "%20s" % "Finished\n"


def get_matchup_history(teams):

    print "-"*80
    print "\nPrevious match-ups\n"
    print "-"*80
    print "\n"

    (home_team, away_team) = teams
    result_count = 0

    for result in results_history:
        if not sorted(result[0]) == sorted(teams):
            continue

        print result
        result_count += 1

    if not result_count:
        print "No previous match-ups"


    print "\n\n"


def get_league_stats():

    driver.find_element_by_xpath('//ul[@class="list-tabs"]//a[contains(text(),"League stats")]').click()

    page = driver.find_element_by_class_name("list-tabs")
    table = driver.find_element_by_class_name("leaguestats")

    for row in table.find_elements_by_xpath(".//tr"):
        if len(row.find_elements_by_tag_name("td")) == 0:
            continue

        data = [str(td.text).strip() for td in row.find_elements_by_tag_name("td")]  # Home - Away, 2:1, home_odds, draw_odds, away_odds, date

        dict_keys = {
            'Matches played': 'matches_played',
            'Matches remaining': 'matches_remaining',
            'Home team wins': 'home_wins',
            'Draws': 'draws',
            'Away team wins': 'away_wins',
            'Goals scored': 'goals_scored',
            'Home goals': 'home_goals',
            'Away goals': 'away_goals',
            'Over 2.5': 'over',
            'Under 2.5': 'under'
        }

        league_stats[dict_keys[data[0]]] = data[1:]  # (Totals, %)   Goals: (Totals, Per Match)


    driver.find_element_by_xpath('//ul[@class="list-tabs"]//a[contains(text(),"Summary")]').click()
    time.sleep(3)


def get_results_history():

    print "%20s" % "Getting Results:", "%20s" % "Started"

    driver.find_element_by_xpath('//ul[@class="list-tabs"]//a[contains(text(),"Results")]').click()
    table = driver.find_element_by_class_name("js-tablebanner-ntb")

    for row in table.find_elements_by_xpath(".//tr"):
        if len(row.find_elements_by_tag_name("td")) == 0:
            continue
        elif "table-main__banner" in row.get_attribute("class"):  # skip banner row box
            continue

        match_data = [str(td.text) for td in row.find_elements_by_tag_name("td")]  # Home - Away, 2:1, home_odds, draw_odds, away_odds, date
        (home_team, away_team) = match_data[0].split(" - ")

        bad_match = False

        for data in match_data:
            if 'POSTP' in data:
                bad_match = True

        if not bad_match:
            results_history.append([(home_team, away_team), match_data[1:-1]])


    driver.find_element_by_xpath('//ul[@class="list-tabs"]//a[contains(text(),"Summary")]').click()
    time.sleep(5)

    print "%20s" % "Getting Results:", "%20s" % "Finished\n"







def favorite_underdog_analysis(teams):

    print "-"*80
    print "\nFavorite - Underdog analysis\n"
    print "-"*80
    print "\n"

    analyze_home_team(teams[0])
    analyze_away_team(teams[1])

    print "\n"

def analyze_home_team(test_team_name):
    # get_result_history()
    home_results = []

    home_favorite_win = 0
    home_favorite_loss = 0
    home_favorite_draw = 0

    home_underdog_win = 0
    home_underdog_loss = 0
    home_underdog_draw = 0


    score_sum = 0
    over_count = 0
    scored_count = 0
    score_delta = 0
    scores = []

    for result in results_history:
        (home_team, away_team) = result[0]
        if not home_team == test_team_name:
            continue

        if home_team == test_team_name:
            home_results.append(result)



    for result in home_results:
        (test_team, opponent) = result[0]
        (test_team_score, opponent_score) = [int(x) for x in result[1][0].split(":")]
        (test_team_odds, draw_odds, opponent_odds) = result[1][1:]

        score_sum += test_team_score
        scores.append(test_team_score)

        delta = abs(team_rankings_overall.index(test_team) - team_rankings_overall.index(opponent))

        score_delta += abs(test_team_score - opponent_score)

        if test_team_score > 0:
            scored_count += 1

        if (test_team_score + opponent_score) > 2.5:
            over_count += 1

        if (test_team_score > opponent_score):
            if (test_team_odds < opponent_odds):
                home_favorite_win += 1                    # Won as favorite
            else:
                home_underdog_win += 1                    # Won as underdog
        elif (int(test_team_score) < int(opponent_score)):
            if (test_team_odds < opponent_odds):          # Lost as favorite
                home_favorite_loss += 1
            else:
                home_underdog_loss += 1                   # Lost as underdog
        else:
            if (test_team_odds < opponent_odds):
                home_favorite_draw += 1                   # Drew as favorite
            else:
                home_underdog_draw += 1                   # Drew as underdog

    match_count = len(home_results)
    win_rate = int((home_favorite_win + home_underdog_win)/len(home_results)*100) if len(home_results) > 0 else 0
    over_rate = int(over_count/len(home_results)*100) if len(home_results) > 0 else 0
    scored_rate = int(scored_count/len(home_results)*100) if len(home_results)> 0 else 0

    print test_team_name, "  @ HOME"
    print "-" * 8, "\n"
    print "%15s" % "Win rate:", win_rate, " %"
    print "%15s" % "Over rate:", over_rate, " %"
    print "%15s" % "Scored rate:", scored_rate, " %", "\n"


    print "Home - Favorite:", "%d - %d - %d" % (home_favorite_win, home_favorite_draw, home_favorite_loss)
    print "Home - Underdog:", "%d - %d - %d" % (home_underdog_win, home_underdog_draw, home_underdog_loss)
    print "\n"


    avg_goals = score_sum/match_count
    get_poisson_tuples(avg_goals)




def get_poisson_tuples(avg_goals):

    iterations = 10000
    poisson = np.random.poisson(avg_goals, iterations)
    counter = Counter(poisson)
    goals_range = range(0, len(counter.most_common()))
    percentages = []


    print "\nPoisson distribution ( > )\t", round(avg_goals, 2)

    for x in goals_range:
        cumulative_count = 0

        for y in goals_range[::-1]:
            if y > x:
                cumulative_count += counter[y]

        percentage = 100*(cumulative_count/iterations)
        if percentage > 5:
            print x, "%7s" % percentage, "%"

    print "\n\n"


def analyze_away_team(test_team_name):

    away_results = []

    away_favorite_win = 0
    away_favorite_loss = 0
    away_favorite_draw = 0

    away_underdog_win = 0
    away_underdog_loss = 0
    away_underdog_draw = 0

    score_sum = 0
    over_count = 0
    scored_count = 0
    score_delta = 0
    scores = []

    for result in results_history:
        (home_team, away_team) = result[0]
        if not away_team == test_team_name:
            continue
        away_results.append(result)

    for result in away_results:
        (opponent, test_team) = result[0]
        (opponent_score, test_team_score) = [int(x) for x in result[1][0].split(":")]
        (opponent_odds, draw_odds, test_team_odds) = result[1][1:]


        score_sum += test_team_score
        scores.append(test_team_score)

        delta = abs(team_rankings_overall.index(test_team) - team_rankings_overall.index(opponent))

        score_delta += abs(test_team_score - opponent_score)

        if test_team_score > 0:
            scored_count += 1

        if test_team_score + opponent_score > 2.5:
            over_count += 1

        if (test_team_score > opponent_score):
            if (test_team_odds < opponent_odds):
                away_favorite_win += 1                          # Won as favorite
            else:
                away_underdog_win += 1                          # Won as underdog
        elif (int(test_team_score) < int(opponent_score)):
            if (test_team_odds < opponent_odds):                # Lost as favorite
                away_favorite_loss += 1
            else:
                away_underdog_loss += 1                         # Lost as underdog
        else:
            if (test_team_odds < opponent_odds):
                away_favorite_draw += 1                         # Drew as favorite
            else:
                away_underdog_draw += 1  # Drew as underdog


    match_count = len(away_results)
    win_rate = int((away_favorite_win + away_underdog_win)/len(away_results)*100) if len(away_results) > 0 else 0
    over_rate = int(over_count/len(away_results)*100) if len(away_results) > 0 else 0
    scored_rate = int(scored_count/len(away_results)*100) if len(away_results)> 0 else 0

    print test_team_name, "  @ AWAY"
    print "-" * 8, "\n"
    print "%15s" % "Win rate:", win_rate, "%"
    print "%15s" % "Over rate:", over_rate, "%"
    print "%15s" % "Scored rate:", scored_rate, " %", "\n"


    print "Away - Favorite:", "%d - %d - %d" % (away_favorite_win, away_favorite_draw, away_favorite_loss)
    print "Away - Underdog:", "%d - %d - %d" % (away_underdog_win, away_underdog_draw, away_underdog_loss)
    print "\n"

    avg_goals = score_sum/match_count
    get_poisson_tuples(avg_goals)

def ranking_delta_analysis(teams):

    # Get similar RankDelta matchups
    # How often did Home Favorite score?
    # How often did Away Favorite score
    # ...


    (home_team, away_team) = teams
    delta = abs(team_rankings_overall.index(home_team) - team_rankings_overall.index(away_team))
    delta_padding = 1

    print "-"*80
    print "\nRanking delta analysis\n"
    print "Ranking delta:\t", delta
    print "Delta padding:\t", delta_padding, "\n"

    print "-"*80


    # match_count = (count, goal_diff_sum, o2.5, btts)
    home_favorite_count = [0, 0, 0, 0]
    home_underdog_count = [0, 0, 0, 0]
    away_favorite_count = [0, 0, 0, 0]
    away_underdog_count = [0, 0, 0, 0]
    draw_home_favorite_count = [0, 0, 0, 0]
    draw_away_favorite_count = [0, 0, 0, 0]

    # print "%35s" % "RESULT", "%10s" % "RDelta", "%10s" % "GDelta"

    x, y = [], []


    for result in results_history:



        # result = [(home_team, away_team), [score, home_odds, draw_odds, away_odds]]
        (home_team, away_team) = result[0]
        (score, home_odds, draw_odds, away_odds) = result[1]

        if not ":" in score:
            # result[1] for postponed games ['POSTP.', ' ', ' ', ' ']
            continue

        (home_score, away_score) = score.split(":")
        odds_ratio = round(float(home_odds)/float(away_odds), 2)
        # if odds_ratio < .5:
        #     print result
        #     print "Odds ratio", odds_ratio

        # x.append(odds_ratio)
        # y.append()
        # y.append(int(home_score) - int(away_score))

        test_delta = abs(team_rankings_overall.index(home_team) - team_rankings_overall.index(away_team))

        if (delta - delta_padding) <= test_delta <= (delta + delta_padding):

            (home_score, away_score) = result[1][0].split(":")
            (home_odds, draw_odds, away_odds) = result[1][1:]
            goal_diff = abs(int(home_score) - int(away_score))
            result_str = 'Winner:\t'


            if (int(home_score) > int(away_score)):     # Home team won
                result_str += "HOME\t"

                if (home_odds < away_odds):             # Home team was favorite
                    result_str += "Favorite"
                    home_favorite_count[0] += 1
                    home_favorite_count[1] += goal_diff
                    if int(home_score)+int(away_score) > 2.5:
                        home_favorite_count[2] += 1
                else:
                    result_str += "Underdog"
                    home_underdog_count[0] +=  1
                    home_underdog_count[1] += goal_diff
                    if int(home_score) + int(away_score) > 2.5:
                        home_underdog_count[2] += 1
            elif (int(home_score) < int(away_score)):                                       # Away team won
                result_str += "AWAY\t"

                if (away_odds < home_odds):              # Away team was favorite
                    result_str += "Favorite"
                    away_favorite_count[0] += 1
                    away_favorite_count[1] += goal_diff
                    if int(home_score) + int(away_score) > 2.5:
                        away_favorite_count[2] += 1

                else:
                    result_str += "Underdog"
                    away_underdog_count[0] += 1
                    away_underdog_count[1] += goal_diff
                    if int(home_score) + int(away_score) > 2.5:
                        away_underdog_count[2] += 1
            else:                                                   # Draw
                result_str += "DRAW\t"

                if (home_odds < away_odds):
                    result_str += "Favorite"
                    draw_home_favorite_count[0] += 1
                    if int(home_score) + int(away_score) > 2.5:
                        draw_home_favorite_count[2] += 1
                else:
                    result_str += "Underdog"
                    draw_away_favorite_count[0] += 1
                    if int(home_score) + int(away_score) > 2.5:
                        draw_away_favorite_count[2] += 1
            # print "%25s" % result_str, "%10s" % test_delta, "%10s" % (str(abs(int(home_score) - int(away_score)))),  "\t", result

                # home_favorite_count = [0, 0, 0, 0]
                # home_underdog_count = [0, 0, 0, 0]
                # away_favorite_count = [0, 0, 0, 0]
                # away_underdog_count = [0, 0, 0, 0]
                # draw_home_favorite_count = [0, 0, 0, 0]
                # draw_away_favorite_count = [0, 0, 0, 0]



    # print x
    # print y
    # plt.scatter(x, y)
    # plt.show()

    print "\n\n"
    print "HOME - Favorite"
    print "-" * 15, "\n"
    print "%10s" % " ", "%5s" % "#", "%4s" % "WR", "%4s" % "GD", "%4s" % "o2.5"


    home_favorite_labels = [
        ('Home', home_favorite_count),
        ('Away', away_underdog_count),
        ('Draw', draw_home_favorite_count)
    ]

    for winner,_list in home_favorite_labels:
        (game_count, total_games) = (_list[0], home_favorite_count[0] + away_underdog_count[0] + draw_home_favorite_count[0])
        game_percentage = 100*game_count/total_games if total_games > 0 else 0
        goal_diff = _list[1]/game_count if game_count > 0 else 0
        over_count = 100*_list[2]/game_count if game_count > 0 else 0

        print "%10s" % ("%s won:" % winner), "%5d" % game_count, "%.1f" % game_percentage , "%.2f" % goal_diff, "%.2f" % over_count


    print "\n"
    print "AWAY - Favorite"
    print "-" * 15, "\n"
    print "%10s" % " ", "%5s" % "#", "%4s" % "WR", "%4s" % "GD", "%4s" % "o2.5"

    away_favorite_labels = [
        ('Home', home_underdog_count),
        ('Away', away_favorite_count),
        ('Draw', draw_away_favorite_count)
    ]

    for winner, _list in away_favorite_labels:
        (game_count, total_games ) = (_list[0], away_favorite_count[0] + home_underdog_count[0] + draw_away_favorite_count[0])

        game_percentage = 100*game_count/total_games if total_games > 0 else 0
        goal_diff = _list[1]/game_count if game_count > 0 else 0
        over_count = 100*_list[2]/game_count if game_count > 0 else 0

        print "%10s" % ("%s won:" % winner), "%5d" % game_count, "%.1f" % game_percentage, "%.2f" % goal_diff, "%.2f" % over_count

    print "\n"

def form_analysis(teams):
    # form_dict[form_type][team_name] = {
    #     'wins': form_data[0],
    #     'draws': form_data[1],
    #     'losses': form_data[2],
    #     'goals_scored': goals_scored,
    #     'goals_allowed': goals_allowed,
    #     'form': form
    # }

    #
    # over_under_dict[table_type][team_name] = {
    #     'over': over_under_data[3],
    #     'under': over_under_data[4],
    #     'goals_scored': goals_scored,
    #     'goals_allowed': goals_allowed,
    #     'goals_per_match': over_under_data[6]
    # }
    (home_team, away_team) = teams


    (home_form, away_form) = (form_dict['home'][home_team], form_dict['away'][away_team])
    (home_ou, away_ou) = (over_under_dict['home'][home_team], over_under_dict['away'][away_team])

    print "-"*80, "\n"
    print "Form analysis", "\n"
    print "-"*80, "\n\n"


    # Overall & Home
    # Home W-D-L goals_scored goals_allowed form

    print "%20s" % " ", "%5s" % "W", "%5s" % "D", "%5s" % "L", "%5s" % "GS", "%5s" % "GA", "   %5s" % "FORM", "\n"


    print "%20s" % home_team, "%5s" % home_form['wins'], "%5s" % home_form['draws'], "%5s" % home_form['losses'], \
        "%5s" % home_form['goals_scored'], "%5s" % home_form['goals_allowed'],  "   %5s" % home_form['form'], "\t Home"
    print "%20s" % " ", "%5s" % form_dict['overall'][home_team]['wins'], "%5s" % form_dict['overall'][home_team]['draws'], "%5s" % form_dict['overall'][home_team]['losses'], \
        "%5s" % form_dict['overall'][home_team]['goals_scored'], "%5s" % form_dict['overall'][home_team]['goals_allowed'],  "   %5s" % form_dict['overall'][home_team]['form'], "\t Overall", "\n"


    print "%20s" % away_team, "%5s" % away_form['wins'], "%5s" % away_form['draws'], "%5s" % away_form['losses'], \
        "%5s" % away_form['goals_scored'], "%5s" % away_form['goals_allowed'],  "   %5s" % away_form['form'], "\t Away"
    print "%20s" % " ", "%5s" % form_dict['overall'][away_team]['wins'], "%5s" % form_dict['overall'][away_team]['draws'], "%5s" % form_dict['overall'][away_team]['losses'], \
        "%5s" % form_dict['overall'][away_team]['goals_scored'], "%5s" % form_dict['overall'][away_team]['goals_allowed'], "   %5s" % form_dict['overall'][away_team]['form'], "\t Overall", "\n\n"


    print "%20s" % " ", "%5s" % "O", "%5s" % "U", "%5s" % "GS", "%5s" % "GA", "%5s" % "GPM", "   %5s" % "FORM","\n"

    print "%20s" % home_team, "%5s" % home_ou['over'], "%5s" % home_ou['under'], "%5s" % home_ou['goals_scored'],\
        "%5s" % home_ou['goals_allowed'], "%5s" % home_ou['goals_per_match'], "   %5s" % home_ou['form'], "\t Home"
    print "%20s" % " ", "%5s" % over_under_dict['overall'][home_team]['over'], "%5s" % over_under_dict['overall'][home_team]['under'], "%5s" % over_under_dict['overall'][home_team]['goals_scored'],\
        "%5s" % over_under_dict['overall'][home_team]['goals_allowed'], "%5s" % over_under_dict['overall'][home_team]['goals_per_match'], "   %5s" % over_under_dict['overall'][home_team]['form'], "\t Overall", "\n"

    print "%20s" % away_team, "%5s" % away_ou['over'], "%5s" % away_ou['under'], "%5s" % away_ou['goals_scored'],\
        "%5s" % away_ou['goals_allowed'], "%5s" % away_ou['goals_per_match'], "   %5s" % away_ou['form'], "\t Away"
    print "%20s" % " ", "%5s" % over_under_dict['overall'][away_team]['over'], "%5s" % over_under_dict['overall'][away_team]['under'], "%5s" % over_under_dict['overall'][away_team]['goals_scored'],\
        "%5s" % over_under_dict['overall'][away_team]['goals_allowed'], "%5s" % over_under_dict['overall'][away_team]['goals_per_match'], "   %5s" % over_under_dict['overall'][away_team]['form'], "\t Overall", "\n\n"

def get_draws():
    draw_list = []
    draw_dict = {}
    for result in results_history:
       #( Home - Away),[ 2:1, home_odds, draw_odds, away_odds, date]
        (home_score, away_score) = result[1][0].split(':')

        if home_score == away_score:
            draw_list.append(result[1][0])


    print Counter(draw_list)



# urls = [



#     ('Brazil_A.txt', 'http://www.betexplorer.com/soccer/brazil/serie-a/'),
#     ('Thailand.txt', 'http://www.betexplorer.com/soccer/thailand/thai-premier-league/'),
#     ('England_Premier.txt', 'http://www.betexplorer.com/soccer/england/premier-league/'),
#     ('Japan_J_League.txt', 'http://www.betexplorer.com/soccer/japan/j-league/')
# ]
# urls = [('Argentina_B.txt', 'http://www.betexplorer.com/soccer/argentina/primera-b-nacional-2016-2017/')]
# urls = [('La_Liga.txt', 'http://www.betexplorer.com/soccer/spain/laliga')]
# urls = [('MLS.txt', 'http://www.betexplorer.com/soccer/usa/mls/')]
urls = [('Japan_J_League.txt', 'http://www.betexplorer.com/soccer/japan/j-league/')]
# urls = [('Thailand.txt', 'http://www.betexplorer.com/soccer/thailand/thai-premier-league/')]
# urls = []

# corner_urls = [('CORNERS_J_League.txt','http://www.totalcorner.com/league/corner_stats/73'),('CORNERS_Thailand.txt', 'http://www.totalcorner.com/league/corner_stats/546')]
corner_urls = []

driver = webdriver.Chrome()

for corner_output_file, url in corner_urls:
    sys.stdout = open(corner_output_file, 'w')
    driver.get(url)

    table = driver.find_element_by_id('corner_table')

    higher_second_half_count = 0
    team_count = 0

    print  "As of:\t", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "\n"


    print "%20s" % "Team", "%15s" % "Avg. get/total", "%10s" % "Mult.", "1H.G", "%5s" % "1H.L", "%5s" % "2H.G", "%5s" % "2H.L"

    for row in table.find_elements_by_xpath(".//tr"):
        if len(row.find_elements_by_tag_name("td")) == 0:
            continue

        team_count += 1
        #                                             5                                              9
        # position, team, matches played, get, lost, avg. get, avg. lost, avg. corners, half get, half lost, avg. half get, avg. half lost

        row_data = [str(td.text) for td in row.find_elements_by_tag_name("td")]  # (EMPTY), Home - Away, ...
        # print row_data

        if not row_data[1]:     # empty team name
            continue

        (first_half_get, first_half_lost) = (int(row_data[8]), int(row_data[9]))
        (get, lost) = (row_data[3], row_data[4])
        (avg_get, avg_total) = (row_data[5], row_data[7])
        (second_half_get, second_half_lost) = (int(get) - int(first_half_get), int(lost) - int(first_half_lost))


        multiplier = str(round(second_half_get/first_half_get, 2))

        if multiplier > 1.1:
            higher_second_half_count += 1


        print "%20s" % row_data[1], "%15s" % str(avg_get + "," + avg_total), "%10s" % multiplier,\
            "%5s" % first_half_get, "%5s" % first_half_lost, "%5s" % second_half_get, "%5s" % second_half_lost

        # print "1st half:", first_half_get, first_half_lost
        # print "2nd half:", second_half_get, second_half_lost
        # print row_data[1], " gets ", round(second_half_get/first_half_get, 2), " times more in the 2nd half."
        # print row_data[1], " loses ", round(second_half_lost/first_half_lost, 2), " times more in the 2nd half."



    print "\n"
    print higher_second_half_count, "/", team_count, " teams score more in the 2nd half"



for output_file, url in urls:
    sys.stdout = open(output_file, 'w')
    driver.get(url)


    next_matches = []
    team_rankings_overall = []
    team_rankings_dict = {}
    form_dict = {'overall': {}, 'home': {}, 'away': {}}
    over_under_dict = {'overall': {}, 'home': {}, 'away': {}}
    results_history = []
    league_stats = {}




    get_next_matches()
    get_rankings()
    get_results_history()
    # get_poisson()
    get_form()
    get_over_under()
    get_league_stats()


    for match in next_matches:
        # match = [(home_team, away_team), [home_odds, draw_odds, away_odds, date_and_time]]

        teams = (home_team, away_team) = match[0]
        (home_odds, draw_odds, away_odds, date_and_time) = match[1]

        print "X"*100, "\n"
        print "%s  v  %s" % (home_team, away_team), "\t"
        print date_and_time, "\n"
        print "1 x 2:\t", "%s %s %s" % (home_odds, draw_odds, away_odds)
        print "\n\n"


        get_matchup_history(teams)
        form_analysis(teams)
        favorite_underdog_analysis(teams)
        ranking_delta_analysis(teams)


    if not next_matches:
        for result in results_history:
            teams = (home_team, away_team) = result[0]
            (score, home_odds, draw_odds, away_odds) = result[1]

            print "X" * 100, "\n"
            print "%s  v  %s" % (home_team, away_team), "\t"
            # print date_and_time, "\n"
            print "1 x 2:\t", "%s %s %s" % (home_odds, draw_odds, away_odds)
            print "\n\n"

            get_matchup_history(teams)
            form_analysis(teams)
            favorite_underdog_analysis(teams)
            ranking_delta_analysis(teams)




driver.quit()


