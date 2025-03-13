import base64
import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from odoo import http
from odoo.http import request


class CaptchaController(http.Controller):

    @http.route('/captcha/generate', type='json', auth='public', csrf=False)
    def generate_captcha(self):
        """ Generate CAPTCHA image and store the correct value in the session """
        captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        request.session['captcha_text'] = captcha_text  # Store in session

        # Generate CAPTCHA image
        img = Image.new('RGB', (150, 50), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((20, 15), captcha_text, fill=(0, 0, 0), font=font)

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        captcha_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {'captcha_image': captcha_image}

    @http.route('/captcha/validate', type='json', auth='public', csrf=False)
    def validate_captcha(self, user_input):
        """ Validate CAPTCHA input """
        correct_captcha = request.session.get('captcha_text', '')
        return {'success': user_input.upper() == correct_captcha,
                'message': 'Invalid CAPTCHA!' if user_input.upper() != correct_captcha else 'Valid CAPTCHA'}

