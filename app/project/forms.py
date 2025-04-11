"""
NEXDB - Project forms
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email

class ProjectForm(FlaskForm):
    """Form for creating and editing projects."""
    name = StringField('Project Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Save Project')


class ProjectMemberForm(FlaskForm):
    """Form for adding members to a project."""
    email = StringField('User Email', validators=[DataRequired(), Email()])
    access_level = SelectField('Access Level', 
                              choices=[
                                  ('read', 'Read Only'),
                                  ('write', 'Read & Write'),
                                  ('admin', 'Admin')
                              ],
                              default='read')
    submit = SubmitField('Add Member') 