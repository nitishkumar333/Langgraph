from django.db import models

class Node(models.Model):
    data = models.JSONField()

    def __str__(self):
        return f"Node {self.id}"

class Edge(models.Model):
    # source = models.ForeignKey(Node, related_name='outgoing_edges', on_delete=models.CASCADE)
    # target = models.ForeignKey(Node, related_name='incoming_edges', on_delete=models.CASCADE)
    data = models.JSONField()

class Message(models.Model):
    content = models.TextField()
    type = models.CharField(max_length=10, choices=[
        ('user', 'user'),
        ('bot', 'bot'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content}"