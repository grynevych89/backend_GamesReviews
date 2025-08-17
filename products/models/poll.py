from django.db import models
from django.core.files.storage import default_storage
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver


class Poll(models.Model):
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Title',
    )
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='polls')
    question = models.CharField("Вопрос", max_length=255)

    image = models.ImageField(
        upload_to='polls/%Y/%m/',
        blank=True, null=True,
        verbose_name='Question image'
    )

    def __str__(self):
        return self.question


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField("Вариант ответа", max_length=255)

    def __str__(self):
        return self.text


@receiver(pre_save, sender=Poll)
def _delete_old_poll_image_on_change(sender, instance: Poll, **kwargs):
    if not instance.pk:
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    old_name = getattr(getattr(old_instance, "image", None), "name", None)
    new_name = getattr(getattr(instance, "image", None), "name", None)

    if old_name and old_name != new_name:
        try:
            default_storage.delete(old_name)
        except Exception:
            pass


@receiver(post_delete, sender=Poll)
def _delete_poll_image_on_delete(sender, instance: Poll, **kwargs):
    name = getattr(getattr(instance, "image", None), "name", None)
    if name:
        try:
            default_storage.delete(name)
        except Exception:
            pass