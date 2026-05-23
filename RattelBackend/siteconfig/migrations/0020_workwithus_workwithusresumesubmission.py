from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('siteconfig', '0019_alter_aboutus_trust_logo_section_links'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkWithUs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hero_title', models.CharField(max_length=255, verbose_name='Hero Title')),
                ('hero_description', models.TextField(verbose_name='Hero Description')),
                ('hero_image', models.FileField(blank=True, null=True, upload_to='workwithus/hero/', verbose_name='Hero Image')),
                ('collaboration_section_title', models.CharField(max_length=255, verbose_name='Collaboration Section Title')),
                ('collaboration_section_description', models.TextField(verbose_name='Collaboration Section Description')),
                ('collaboration_section_step1_title', models.CharField(max_length=255, verbose_name='Collaboration Section Step 1 Title')),
                ('collaboration_section_step1_description', models.TextField(verbose_name='Collaboration Section Step 1 Description')),
                ('collaboration_section_step2_title', models.CharField(max_length=255, verbose_name='Collaboration Section Step 2 Title')),
                ('collaboration_section_step2_description', models.TextField(verbose_name='Collaboration Section Step 2 Description')),
                ('collaboration_section_step3_title', models.CharField(max_length=255, verbose_name='Collaboration Section Step 3 Title')),
                ('collaboration_section_step3_description', models.TextField(verbose_name='Collaboration Section Step 3 Description')),
                ('counter_section_item1_label', models.CharField(max_length=100, verbose_name='Counter Section Item 1 Label')),
                ('counter_section_item1_value', models.PositiveIntegerField(default=0, verbose_name='Counter Section Item 1 Value')),
                ('counter_section_item2_label', models.CharField(max_length=100, verbose_name='Counter Section Item 2 Label')),
                ('counter_section_item2_value', models.PositiveIntegerField(default=0, verbose_name='Counter Section Item 2 Value')),
                ('counter_section_item3_label', models.CharField(max_length=100, verbose_name='Counter Section Item 3 Label')),
                ('counter_section_item3_value', models.PositiveIntegerField(default=0, verbose_name='Counter Section Item 3 Value')),
                ('counter_section_item4_label', models.CharField(max_length=100, verbose_name='Counter Section Item 4 Label')),
                ('counter_section_item4_value', models.PositiveIntegerField(default=0, verbose_name='Counter Section Item 4 Value')),
                ('main_content_section_title', models.CharField(max_length=255, verbose_name='Main Content Section Title')),
                ('main_content_section_tab1_title', models.CharField(max_length=255, verbose_name='Main Content Section Tab 1 Title')),
                ('main_content_section_tab1_description', models.TextField(verbose_name='Main Content Section Tab 1 Description')),
                ('main_content_section_tab2_title', models.CharField(max_length=255, verbose_name='Main Content Section Tab 2 Title')),
                ('main_content_section_tab2_description', models.TextField(verbose_name='Main Content Section Tab 2 Description')),
                ('main_content_section_tab3_title', models.CharField(max_length=255, verbose_name='Main Content Section Tab 3 Title')),
                ('main_content_section_tab3_description', models.TextField(verbose_name='Main Content Section Tab 3 Description')),
                ('advertisement_section_title', models.CharField(max_length=255, verbose_name='Advertisement Section Title')),
                ('advertisement_section_description', models.TextField(verbose_name='Advertisement Section Description')),
                ('advertisement_section_link', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workwithus_advertisement_links', to='siteconfig.link', verbose_name='Advertisement Section Link')),
                ('hero_link', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workwithus_hero_links', to='siteconfig.link', verbose_name='Hero Link')),
            ],
            options={
                'verbose_name': 'Work With Us',
                'verbose_name_plural': 'Work With Us',
            },
        ),
        migrations.CreateModel(
            name='WorkWithUsResumeSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, verbose_name='Full Name')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('phone_number', models.CharField(max_length=50, verbose_name='Phone Number')),
                ('message', models.TextField(verbose_name='Message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('work_with_us', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resume_submissions', to='siteconfig.workwithus', verbose_name='Work With Us')),
            ],
            options={
                'verbose_name': 'Work With Us Resume Submission',
                'verbose_name_plural': 'Work With Us Resume Submissions',
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='workwithusresumesubmission',
            index=models.Index(fields=['-created_at'], name='siteconfig_w_created_926eeb_idx'),
        ),
        migrations.AddIndex(
            model_name='workwithusresumesubmission',
            index=models.Index(fields=['email'], name='siteconfig_w_email_5a3fe9_idx'),
        ),
    ]
