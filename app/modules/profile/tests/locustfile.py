from locust import HttpUser, TaskSet, task
from core.environment.host import get_host_for_locust_testing

class ProfileBehavior(TaskSet):
    def on_start(self):
        self.load_edit_profile()

    @task
    def load_edit_profile(self):
        response = self.client.get("/profile/edit")
        if response.status_code != 200:
            print(f"Failed to load profile edit page: {response.status_code}")

class ProfileUser(HttpUser):
    tasks = [ProfileBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
