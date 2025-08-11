from django.db import models

class Poll(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='polls')
    question = models.CharField("Вопрос", max_length=255)

    def __str__(self):
        return self.question


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField("Вариант ответа", max_length=255)

    def __str__(self):
        return self.text
