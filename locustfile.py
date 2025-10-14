from locust import HttpUser, between, task


class Service1User(HttpUser):
    wait_time = between(1, 2)  # Wait time between requests (1 to 2 seconds)

    @task
    def request_service2(self):
        # Simulate the request from Service 1 to Service 2
        response = self.client.get("/content")
        if response.status_code == 200:
            print("Content received:", response.text)
        else:
            print(f"Failed request. Status code: {response.status_code}")
