import csv, os, random
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

load_dotenv()

SUBJECT = "SHHH Greetings from the Secret Santa Bot!"

CHARSET = "UTF-8"

BODY_TEXT = """
I've got a secret for you, {santa}!

You have been assigned {recip} to be your recipient for this year's Secret Santa!

{recip} has given you this hint....
{comments}

A reminder:
- All gifts must be under $25
- All participants bring ONE gift for the White Elephant
- All participants bring ONE gift for their Secret Santa (I bet {recip} is exited  😉 )

Have a very Merry Christmas!

The Secret Santa Bot 🎅

"""

client = boto3.client('ses',region_name=os.environ['AWS_REGION'])

participants = csv.DictReader(open('Schefer Christmas Bonanza 2021.csv'))

emails = list()
people = dict()

for row in participants:
    email = row['What is your email?']
    emails.append(email)
    people[email] = {
        'name': row['What is your name?'],
        'email': email,
        'comments': row['Comments or requests to help your santa?']
    }

unassigned_emails = emails.copy()
matches = dict()
depth = 0

def handle_matching():
    global unassigned_emails
    global matches
    global depth
    for email in emails:
        choice = random.choice(unassigned_emails)
        while choice == email and len(unassigned_emails) > 1:
            choice = random.choice(unassigned_emails)
        matches[email] = choice
        unassigned_emails.remove(choice)
    if any([santa == recip for santa, recip in matches.items()]) and depth < 1:
        matches = dict()
        unassigned_emails = emails.copy()
        depth += 1
        handle_matching()

handle_matching()
if len(unassigned_emails) > 0:
    print('Matching failed for')
    print(unassigned_emails)
    exit(1)

failed_matches = dict()
for santa, recip in matches.items():
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [people[santa]['email']]
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT.format(santa=people[santa]['name'], recip=people[recip]['name'], comments=people[recip]['comments'])
                    }
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT
                }
            },
            Source=os.environ['SENDER_EMAIL'],
        )
        pass
    except ClientError as e:
        failed_matches[santa] = recip
        print(e.response['Error']['Message'])
    else:
        with open('{recip}.txt'.format(recip=recip), 'w') as f:
            f.write(santa)
            f.close()
        print('Email Sent to {santa}'.format(santa=santa))
if len(failed_matches.keys()) > 0:
    with open('failed.txt', 'w') as f:
        for santa, recip in failed_matches.items():
            f.write('{santa}: {recip}\n'.format(santa=santa, recip=recip))
        f.close()