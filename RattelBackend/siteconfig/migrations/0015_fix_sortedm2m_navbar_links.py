from django.db import migrations
import sortedm2m.fields
from sortedm2m.operations import AlterSortedManyToManyField


class Migration(migrations.Migration):

    dependencies = [
        ('siteconfig', '0014_alter_sitenavbar_navbar_links'),
    ]

    operations = [
        AlterSortedManyToManyField(
            model_name='sitenavbar',
            name='navbar_links',
            field=sortedm2m.fields.SortedManyToManyField(
                blank=True,
                related_name='navbar_links',
                to='siteconfig.link',
                verbose_name='Navbar Links',
            ),
        ),
    ]
