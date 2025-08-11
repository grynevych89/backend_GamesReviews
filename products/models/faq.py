from django.db import models

class FAQ(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255, verbose_name='Question', blank=True)
    answer = models.CharField(max_length=512, verbose_name='Answer', blank=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question
