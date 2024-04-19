from wtforms import Form, StringField, validators, SelectField


class payment (Form):
    card_number = StringField('Card Num (include 1 space after 4 numbers)', [validators.Length(min=19, max=19, message='Card number must be 16 digits with spaces'), validators.Regexp(r'^\d{4} \d{4} \d{4} \d{4}$', message='Invalid card number format (XXXX XXXX XXXX XXXX)'), validators.DataRequired(message='Card number is required')])
    expiration_date = StringField('Expiration Date (mm/yy)', [validators.Length(min=5, max=5, message='Invalid expiration date format'), validators.Regexp(r'^(0[1-9]|1[0-2])\/\d{2}$', message='Invalid expiration date format (mm/yy)'), validators.DataRequired(message='Expiration date is required')])
    cvv = StringField('CVV', [validators.Length(min=3, max=3, message='CVV must be 3 digits'), validators.Regexp(r'^\d{3}$', message='CVV must be 3 digits'), validators.DataRequired(message='CVV is required')])
    card_name = StringField('Card Name (all caps)', [validators.Regexp(r'^[A-Z ]+$', message='Card name should be in all caps and contain only letters and spaces'), validators.DataRequired(message='Card name is required')])


class collection_type (Form):
    collection_type = SelectField('Collection Type', choices=[('pickup', 'In-Store Pickup'), ('delivery', 'Delivery')],)
