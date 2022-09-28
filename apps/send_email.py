from . import mailjet


def send_email(to, subject, text_part, html_part, custom_id):
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "kingsto23@gmail.com",
                    "Name": "Forge"
                },
                "To": [
                    {
                        "Email": to,
                        "Name": to
                    }
                ],
                "Subject": subject,
                "TextPart": text_part,
                "HTMLPart": html_part,  # "<h3>Dear passenger 1, welcome to <a href='https://www.mailjet.com/'>Mailjet</a>!</h3><br />May the delivery force be with you!",
                "CustomID": custom_id
            }
        ]
    }
    result = mailjet.send.create(data=data)
    print("EMAIL STATUS HERE:")
    print(result.status_code)
    print(result.json())
