# -*- encoding: utf-8 -*-

# from turtle import width
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FieldList, DateField, BooleanField, SelectMultipleField, IntegerField
from wtforms.validators import Email, DataRequired
from wtforms.widgets import html_params
from apps.models.scraper import Scrape

# scraper

def select_multi_checkbox(field, ul_class='', **kwargs):
    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)
    html = ['<ul %s>' % html_params(id=field_id, class_=ul_class)]
    for value, label, checked in field.iter_choices():
        choice_id = '%s-%s' % (field_id, value)
        options = dict(kwargs, name=field.name, value=value, id=choice_id)
        if checked:
            options['checked'] = 'checked'
        html.append('<li><input %s /> ' % html_params(**options))
        html.append('<label for="%s">%s</label></li>' % (field_id, label))
    html.append('</ul>')
    return ''.join(html)

class ScraperForm(FlaskForm):
    email = StringField('Email',
                        id='email',
                        validators=[DataRequired()])
    keywords = StringField('Keywords',
                           id='keywords',
                           validators=[DataRequired()])
    start_date = DateField('Start Date',
                           id='start_date',
                           validators=[DataRequired()])
    end_date = DateField('End Date',
                         id='end_date',
                         validators=[DataRequired()])
    engine_options = SelectMultipleField('Engine Options', choices=[
                                         'Duckduckgo News', 'Google News', 'SearX'])
    
    


class TwitterForm(FlaskForm):
    email = StringField('Email',
                        id='email',
                        validators=[DataRequired()])
    keywords = StringField('Keywords',
                           id='keywords',
                           validators=[DataRequired()])
    limit = StringField('Limit',
                        id='limit',
                        validators=[DataRequired()])
    remove_dups = BooleanField('Remove Dups',
                               id='remove_dups',
                               validators=[DataRequired()])

class SIPortalForm(FlaskForm):
    project = StringField('Project',
                            id='project',
                            validators=[DataRequired()])
    category = StringField('Category',
                            id='category',
                            validators=[DataRequired()])
    sub_category = StringField('Sub Category',
                            id='sub_category',
                            validators=[DataRequired()])
    attribute = StringField('Attribute',
                            id='attribute',
                            validators=[DataRequired()])
    article_date = StringField('Article Date',
                            id='article_date',
                            validators=[DataRequired()])
    city = StringField('City',
                            id='city',
                            validators=[DataRequired()])
    location = StringField('Location',
                            id='location',
                            validators=[DataRequired()])
    author = StringField('Author',
                            id='author',
                            validators=[DataRequired()])
    source = StringField('Source',
                            id='source',
                            validators=[DataRequired()])
    link = StringField('Link',
                            id='link',
                            validators=[DataRequired()])
    article_title = StringField('Article Title',
                            id='article_title',
                            validators=[DataRequired()])
    summary_title = StringField('Summary Title',
                            id='summary_title',
                            validators=[DataRequired()])
    article_text = StringField('Article Text',
                            id='article_text',
                            validators=[DataRequired()])

class Report(FlaskForm):
    id = IntegerField(primary_key=True)
    current_reviewer_id = IntegerField()
    # current_reviewer = relationship("Reviewer")
    article_source =    StringField('Article Source', id='article_source', validators=[DataRequired()])
    article_title =     StringField('Article Title', id='article_title', validators=[DataRequired()])
    article_text =      StringField('Article Text', id='article_text', validators=[DataRequired()])
    attributes =        StringField('Attributes', id='attributes', validators=[DataRequired()])
    category =          StringField('Category', id='category', validators=[DataRequired()])
    city =              StringField('City', id='city', validators=[DataRequired()])
    incident_date =     StringField('Incident Date', id='incident_date', validators=[DataRequired()])
    location =          StringField('Location', id='location', validators=[DataRequired()])
    project =           StringField('Project', id='project', validators=[DataRequired()])
    sub_category =      StringField('Sub Category', id='sub_category', validators=[DataRequired()])