import os
import json


class GitHubTestState:

    def __init__(self, app_id):
        self.state = {}
        directory = os.path.expanduser('~/.github-test-state')
        self.state_path = os.path.join(directory, f'{app_id}.json')
        if not os.path.exists(directory):
            os.mkdir(directory)
        if not self.load():
            self.save()

    def load(self):
        if os.path.exists(self.state_path):
            with open(self.state_path) as fp:
                self.state = json.load(fp)
                return True
        return False

    def save(self):
        with open(self.state_path, 'w') as fp:
            json.dump(self.state, fp)

    def __setitem__(self, key, value):
        self.state[key] = value
        self.save()

    def __getitem__(self, item):
        return self.state[item]

    def get(self, key, default=None):
        return self.state.get(key, default)
