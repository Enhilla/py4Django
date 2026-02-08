from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("complaints", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="is_anonymous",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="TicketRating",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("rater_name", models.CharField(blank=True, max_length=120)),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ratings", to="complaints.ticket")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
