from locust import HttpUser, task, between


class LLMUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def check_health(self):
        """Lightweight health check endpoint."""
        self.client.get("/health")

    @task(1)
    def generate_llm(self):
        """Heavy LLM generation endpoint."""
        payload = {"prompt": "Write 10 characters."}
        self.client.post("/generate", json=payload, timeout=60)
