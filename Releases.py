import sys
import requests
import json
from datetime import datetime


class Releases:
    def __init__(self, github_pgdb, github_url, headers, org, repo):
        self.github_pgdb = github_pgdb
        self.github_url = github_url
        self.headers = headers
        self.org = org
        self.repo = repo

    def run_github_releases(self):
        print("Running releases")

        releases_url = f"{self.github_url}/repos/{self.org}/{self.repo}/releases?state=all&page=1&per_page=100"
        releases = self.get_github_releases(releases_url, self.headers)
        self.process_releases(self.org, self.repo, releases)

    def get_github_releases(self, releases_url, headers):
        print("Getting a list of releases from Github")

        response = requests.get(releases_url, headers=headers)
        releases = response.json()

        while 'next' in response.links.keys():
            print("Getting page: " + response.links['next']['url'])
            response = requests.get(response.links['next']['url'], headers=headers)
            releases.extend(response.json())

        return releases

    # noinspection PyBroadException
    def process_releases(self, org, repo, releases):
        print("Adding or updating releases in database")

        repo_id = self.get_repo_id(org, repo)
        for release in releases:
            try:
                result = self.release_exists_in_db(repo_id, release["id"])

                if not result:
                    self.add_release_to_db(repo_id, release)
                else:
                    self.update_release_in_db(repo_id, release)
            except:
                e = sys.exc_info()[0]
                print("Error. Likely cannot connect to database: %s " % e)
                return

    def get_repo_id(self, org, repo):
        cursor = self.github_pgdb.cursor()
        repo_id = 0
        sql = "SELECT repo_id FROM repos WHERE org = '" + org + "' AND name = '" + repo + "'"

        cursor.execute(sql)
        result = cursor.fetchone()

        if result:
            repo_id = result[0]

        cursor.close()

        return repo_id

    def release_exists_in_db(self, repo_id, release_id):
        cursor = self.github_pgdb.cursor()
        release_exists = False

        sql = "SELECT release_id FROM releases WHERE release_id = " + str(release_id) + \
              " AND repo_id = " + str(repo_id)

        cursor.execute(sql)
        result = cursor.fetchone()

        if result:
            release_exists = True

        cursor.close()

        return release_exists

    def add_release_to_db(self, repo_id, release):
        print("Adding release " + str(release["id"]))
        cursor = self.github_pgdb.cursor()

        created_at = datetime.strptime(release["created_at"], '%Y-%m-%dT%H:%M:%SZ')

        if release["published_at"]:
            published_at = datetime.strptime(release["published_at"], '%Y-%m-%dT%H:%M:%SZ')
        else:
            published_at = None

        download_count = 0

        for asset in release["assets"]:
            download_count += asset["download_count"]

        prerelease = 0

        if release["prerelease"]:
            prerelease = 1

        sql = "INSERT INTO releases (release_id, repo_id, name, tag_name, prerelease, downloads," \
              " created_at, published_at)" \
              " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

        val = (release["id"], repo_id, release["name"], release["tag_name"], prerelease,
               download_count, created_at, published_at)

        cursor.execute(sql, val)
        self.github_pgdb.commit()

    def update_release_in_db(self, repo_id, release):
        print("Updating release " + str(release["id"]))
        cursor = self.github_pgdb.cursor()

        if release["published_at"]:
            published_at = datetime.strptime(release["published_at"], '%Y-%m-%dT%H:%M:%SZ')
        else:
            published_at = None

        download_count = 0

        for asset in release["assets"]:
            download_count += asset["download_count"]

        prerelease = 0

        if release["prerelease"]:
            prerelease = 1

        sql = "UPDATE releases SET name=%s, tag_name=%s, prerelease=%s, downloads=%s, published_at=%s WHERE " \
              "release_id = %s AND repo_id = %s"
        val = (release["name"], release["tag_name"], prerelease, download_count, published_at, release["id"], repo_id)

        cursor.execute(sql, val)
        self.github_pgdb.commit()
