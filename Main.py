import argparse
import json
import psycopg2
from Issues import Issues
from Releases import Releases


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

        # Github issues
        issues_instance = Issues(github_pgdb, github_url, headers, repo['org'], repo['repo'])
        issues_instance.run_github_issues()

        # Github releases
        releases_instance = Releases(github_pgdb, github_url, headers, repo['org'], repo['repo'])
        releases_instance.run_github_releases()


if __name__ == '__main__':
    main()
