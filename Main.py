import sys
import argparse
import requests
import json
import psycopg2
from datetime import datetime


def get_github_issues(issues_url, headers):
    print("Getting a list of issues from Github")

    response = requests.get(issues_url, headers=headers)
    issues = response.json()

    while 'next' in response.links.keys():
        print("Getting page: " + response.links['next']['url'])
        response = requests.get(response.links['next']['url'], headers=headers)
        issues.extend(response.json())

    return issues


def add_issue_to_db(repo_id, issue):
    print("Adding issue " + str(issue["id"]))
    cursor = github_pgdb.cursor()

    created_at = datetime.strptime(issue["created_at"], '%Y-%m-%dT%H:%M:%SZ')

    if issue["closed_at"]:
        closed_at = datetime.strptime(issue["closed_at"], '%Y-%m-%dT%H:%M:%SZ')
    else:
        closed_at = None

    if "pull_request" in issue:
        pull_request = 1
    else:
        pull_request = 0

    sql = "INSERT INTO issues (issue_id, repo_id, node_id, number, user_id, state," \
          " pull_request, created_at, closed_at, json_data)" \
          " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    val = (issue["id"], repo_id, issue["node_id"], issue["number"], issue["user"]["id"],
           issue["state"], pull_request, created_at, closed_at, json.dumps(issue))

    cursor.execute(sql, val)
    github_pgdb.commit()

    if "labels" in issue:
        add_labels_to_db(issue["id"], issue["labels"])


def update_issue_in_db(repo_id, issue):
    print("Updating issue " + str(issue["id"]))
    cursor = github_pgdb.cursor()

    if issue["closed_at"]:
        closed_at = datetime.strptime(issue["closed_at"], '%Y-%m-%dT%H:%M:%SZ')
    else:
        closed_at = None

    sql = "UPDATE issues SET state=%s, closed_at=%s, json_data=%s WHERE issue_id = %s AND repo_id = %s"
    val = (issue["state"], closed_at, json.dumps(issue), issue["id"], str(repo_id))

    cursor.execute(sql, val)
    github_pgdb.commit()

    current_issue_labels = get_labels_for_issue(issue["id"], repo_id)

    additions = []
    deletions = []

    # Get any additions
    if "labels" in issue:
        update_issue_labels = issue["labels"]
        for label in update_issue_labels:
            label_id = label["id"]
            if len(list(filter(lambda x: x.get("id") == label_id, current_issue_labels))) == 0:
                additions.append(label)

    if len(additions) > 0:
        add_labels_to_db(issue["id"], additions)

    # Get any deletions
    if len(current_issue_labels) > 0:
        if "labels" not in issue:
            deletions.append(current_issue_labels)
        else:
            update_issue_labels = issue["labels"]
            for label in current_issue_labels:
                label_id = label["id"]
                if len(list(filter(lambda x: x.get("id") == label_id, update_issue_labels))) == 0:
                    deletions.append(label)

    if len(deletions) > 0:
        delete_labels_from_db(issue["id"], deletions)


def add_labels_to_db(issue_id, labels):
    print("Adding labels in to the database for issue " + str(issue_id))
    cursor = github_pgdb.cursor()

    for label in labels:
        sql = "INSERT INTO labels (label_id, node_id, issue_id, name)" \
              "VALUES (%s, %s, %s, %s)"

        val = (label["id"], label["node_id"], issue_id, label["name"])

        cursor.execute(sql, val)
        github_pgdb.commit()


def update_labels_in_db(issue_id, labels):
    print("Updating labels in the database for issue " + str(issue_id))
    cursor = github_pgdb.cursor()

    for label in labels:
        sql = "UPDATE SET name = %s WHERE issue_id = %s AND label_id = "
        val = (label["name"], label["id"])

        cursor.execute(sql, val)
        github_pgdb.commit()


def delete_labels_from_db(issue_id, labels):
    print("Deleting labels for issue " + str(issue_id))
    cursor = github_pgdb.cursor()

    for label in labels:
        sql = "DELETE FROM labels WHERE issue_id = " + str(issue_id) + \
              " AND label_id = " + str(label["id"])
        cursor.execute(sql)
        github_pgdb.commit()


def get_labels_for_issue(issue_id, repo_id):
    print("Getting labels from the database for issue " + str(issue_id))
    cursor = github_pgdb.cursor()

    sql = "SELECT labels.label_id, labels.node_id, labels.name FROM labels" \
          " JOIN issues using(issue_id)" \
          " WHERE labels.issue_id = " + str(issue_id) + \
          " AND issues.repo_id = " + str(repo_id)

    cursor.execute(sql)
    records = cursor.fetchall()
    cursor.close()

    labels = []

    for record in records:
        labels.append({"id": record[0], "node_id": record[1], "name": record[2]})

    return labels


def issue_exists_in_db(repo_id, issue_id):
    cursor = github_pgdb.cursor()
    issue_exists = False

    sql = "SELECT issue_id FROM issues WHERE issue_id = " + str(issue_id) + \
          " AND repo_id = " + str(repo_id)

    cursor.execute(sql)
    result = cursor.fetchone()

    if result:
        issue_exists = True

    cursor.close()

    return issue_exists


def get_repo_id(org, repo):
    cursor = github_pgdb.cursor()
    repo_id = 0
    sql = "SELECT repo_id FROM repos WHERE org = '" + org + "' AND name = '" + repo + "'"

    cursor.execute(sql)
    result = cursor.fetchone()

    if result:
        repo_id = result[0]

    cursor.close()

    return repo_id


# noinspection PyBroadException
def process_issues(org, repo, issues):
    print("Adding or updating issues in database")
    repo_id = get_repo_id(org, repo)
    for issue in issues:
        try:
            result = issue_exists_in_db(repo_id, issue["id"])

            if not result:
                add_issue_to_db(repo_id, issue)
            else:
                update_issue_in_db(repo_id, issue)
        except:
            e = sys.exc_info()[0]
            print("Error. Likely cannot connect to database: %s " % e)
            return


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-user", "--user", required=False, default="postgres", help="Name of the postgres user")
    parser.add_argument("-password", "--password", required=True, help="Postgres user password")
    parser.add_argument("-host", "--host", required=False, default="localhost", help="Postgres host name")
    parser.add_argument("-port", "--port", required=False, default="5432", help="Postgres host name")
    parser.add_argument("-database", "--database", required=False, default="ghissues", help="Postgres database name")
    parser.add_argument("-token", "--token", required=True, help="Github token")

    args = vars(parser.parse_args())

    github_token = args["token"]

    headers = {'Authorization': 'token ' + github_token}
    github_url = "https://api.github.com"

    repos = json.load(open('repos.json'))

    global github_pgdb
    github_pgdb = psycopg2.connect(
        user=args["user"],
        password=args["password"],
        host=args["host"],
        port=args["port"],
        database=args["database"]
    )

    for repo in repos["repos"]:
        issues_url = f"{github_url}/repos/{repo['org']}/{repo['repo']}/issues?state=all&page=1&per_page=100"
        issues = get_github_issues(issues_url, headers)
        process_issues(repo['org'], repo['repo'], issues)


if __name__ == '__main__':
    main()
